using System;
using Unity.Collections;
using Unity.Netcode;
using UnityEngine;
using BoardroomXR.Logging;
using BoardroomXR.Network;

namespace BoardroomXR.Identity
{
    /// <summary>
    /// Attached to every player avatar (Netcode for GameObjects NetworkObject).
    /// Holds the identity claim and the *server-authoritative* verification
    /// state. Clients can request verification, but only the server may ever
    /// flip IsVerified to true - this is the property that stops a client
    /// from simply spoofing "verified" locally.
    /// </summary>
    [RequireComponent(typeof(NetworkObject))]
    public class AvatarIdentity : NetworkBehaviour
    {
        [Tooltip("Corporate directory ID this avatar claims to represent (e.g. employee ID).")]
        public NetworkVariable<FixedString64Bytes> ClaimedUserId = new(
            default,
            NetworkVariableReadPermission.Everyone,
            NetworkVariableWritePermission.Owner);

        /// <summary>True only once the server has accepted all MFA factors.</summary>
        public NetworkVariable<bool> IsVerified = new(
            false,
            NetworkVariableReadPermission.Everyone,
            NetworkVariableWritePermission.Server);

        /// <summary>Server timestamp (NetworkManager.ServerTime) of last successful verification.</summary>
        public NetworkVariable<double> VerifiedAtServerTime = new(
            0,
            NetworkVariableReadPermission.Everyone,
            NetworkVariableWritePermission.Server);

        /// <summary>Incremented by SpoofDetector; a rising count without re-verification is a red flag.</summary>
        public NetworkVariable<int> AnomalyStrikes = new(
            0,
            NetworkVariableReadPermission.Everyone,
            NetworkVariableWritePermission.Server);

        /// <summary>
        /// Continuous trust as every participant sees it (v6 trust badge). Written by the
        /// server from the biometric engine, readable by every client, so anyone in the
        /// meeting can see whether the person behind this avatar is still verified.
        /// </summary>
        public NetworkVariable<byte> Trust = new(
            (byte)TrustLevel.SigningIn,
            NetworkVariableReadPermission.Everyone,
            NetworkVariableWritePermission.Server);

        /// <summary>Smoothed biometric score 0-1, replicated for the trust badge (rounded to 1%).</summary>
        public NetworkVariable<byte> TrustPercent = new(
            0,
            NetworkVariableReadPermission.Everyone,
            NetworkVariableWritePermission.Server);

        /// <summary>
        /// Silent duress flag (v6 panic gesture). Set when the wearer drew their signature
        /// backwards. Nothing in the headset shows it; only the security dashboard does.
        /// </summary>
        public NetworkVariable<bool> Duress = new(
            false,
            NetworkVariableReadPermission.Everyone,
            NetworkVariableWritePermission.Server);

        public TrustLevel TrustLevelValue => (TrustLevel)Trust.Value;

        /// <summary>
        /// Raised on the server the moment verification is revoked, carrying the
        /// reason. <see cref="NetworkAuthRelay"/> listens and pushes a re-auth
        /// request down to the affected client.
        /// </summary>
        public event Action<string> OnServerRevoked;

        /// <summary>
        /// Overrides the claimed ID for this run. Set before spawn (e.g. by a
        /// demo participant picker) to test more than one identity on one headset.
        /// </summary>
        public static string LocalClaimedIdOverride;

        public string ClaimedUserIdString => ClaimedUserId.Value.ToString();

        public override void OnNetworkSpawn()
        {
            if (IsOwner)
            {
                // Owner proposes an identity claim; server verifies it during MFA.
                ClaimedUserId.Value = new FixedString64Bytes(SystemInfoIdentityStub.GetLocalClaimedId());
            }

            if (IsServer)
            {
                // Make the access gate aware of this avatar. Without this the gate's
                // registry stays empty and it never gates anything.
                var gate = FindAnyObjectByType<BoardroomAccessGate>();
                if (gate != null) gate.ServerRegisterAvatar(OwnerClientId, this);
                else Debug.LogWarning("[AvatarIdentity] No BoardroomAccessGate found in scene; content gating is inactive.");
            }

            SessionLogger.LogGlobal(
                $"AvatarIdentity spawned. netId={NetworkObjectId} owner={OwnerClientId} " +
                $"isServer={IsServer} isOwner={IsOwner} claimedId={ClaimedUserIdString}");
        }

        public override void OnNetworkDespawn()
        {
            if (IsServer)
            {
                var gate = FindAnyObjectByType<BoardroomAccessGate>();
                if (gate != null) gate.ServerUnregisterAvatar(OwnerClientId);
            }
        }

        /// <summary>Server-side helper: call once every MFA factor has passed.</summary>
        public void ServerMarkVerified()
        {
            if (!IsServer) return;
            IsVerified.Value = true;
            AnomalyStrikes.Value = 0;
            VerifiedAtServerTime.Value = NetworkManager.Singleton != null
                ? NetworkManager.Singleton.ServerTime.Time
                : 0;

            SessionLogger.LogGlobal(
                $"VERIFIED {ClaimedUserIdString} at serverTime={VerifiedAtServerTime.Value:F2}. Strikes reset to 0.");
        }

        /// <summary>Server-side: publishes the trust badge. Only writes when something changed.</summary>
        public void ServerSetTrust(TrustLevel level, float score)
        {
            if (!IsServer) return;
            byte l = (byte)level;
            byte pct = (byte)Mathf.Clamp(Mathf.RoundToInt(score * 100f), 0, 100);
            if (Trust.Value != l) Trust.Value = l;
            if (TrustPercent.Value != pct) TrustPercent.Value = pct;
        }

        /// <summary>Server-side: raises or clears the silent duress alarm.</summary>
        public void ServerSetDuress(bool on, string detail)
        {
            if (!IsServer || Duress.Value == on) return;
            Duress.Value = on;
            SilentAlertLog.Record(ClaimedUserIdString, on ? "DURESS: signature drawn backwards - " + detail : "duress cleared - " + detail);
        }

        /// <summary>Server-side helper: revoke trust immediately (e.g. spoof detected).</summary>
        public void ServerRevokeVerification(string reason = "unspecified")
        {
            if (!IsServer) return;
            if (!IsVerified.Value) return; // already unverified; nothing to revoke

            IsVerified.Value = false;
            SessionLogger.LogGlobal($"REVOKED {ClaimedUserIdString}. Reason: {reason}");
            OnServerRevoked?.Invoke(reason);
        }
    }

    /// <summary>What other participants see on this person's trust badge.</summary>
    public enum TrustLevel : byte { SigningIn = 0, Verified = 1, Warning = 2, StepUp = 3, Learning = 4, Locked = 5 }

    /// <summary>
    /// Security-desk-only log for silent alarms. Deliberately separate from BioEventLog,
    /// which is shown on the in-room SOC wall where whoever forced the login could read it.
    /// </summary>
    public static class SilentAlertLog
    {
        public struct Entry { public string clock, user, text; }
        private static readonly System.Collections.Generic.List<Entry> _entries = new();
        public static System.Collections.Generic.IReadOnlyList<Entry> Entries => _entries;

        public static void Record(string user, string text)
        {
            _entries.Add(new Entry { clock = DateTime.Now.ToString("HH:mm:ss"), user = user, text = text });
            if (_entries.Count > 50) _entries.RemoveAt(0);
            Debug.Log($"[SilentAlert] {user}: {text}");   // logcat only, for the post-session analysis
        }

        public static void Clear() => _entries.Clear();
    }

    /// <summary>Stand-in for whatever real corporate SSO/directory lookup you wire in later.</summary>
    public static class SystemInfoIdentityStub
    {
        public static string GetLocalClaimedId()
        {
            if (!string.IsNullOrWhiteSpace(AvatarIdentity.LocalClaimedIdOverride))
                return AvatarIdentity.LocalClaimedIdOverride;

            string id = SystemInfo.deviceUniqueIdentifier;
            if (string.IsNullOrEmpty(id) || id == SystemInfo.unsupportedIdentifier) id = "LOCAL";
            return "EMP-" + id.Substring(0, Mathf.Min(8, id.Length));
        }
    }
}
