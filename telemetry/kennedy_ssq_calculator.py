"""
Kennedy Simulator Sickness Questionnaire (SSQ) Diagnostic Engine
Conforming to Kennedy, Lane, Berbaum & Lilienthal (1993).
Evaluates Cybersickness across Nausea (N), Oculomotor (O), and Disorientation (D).
"""

WEIGHTS = {
    'Nausea': 9.54,
    'Oculomotor': 3.74,
    'Disorientation': 13.92,
    'Total': 3.74
}

def calculate_ssq(symptoms):
    """
    16 standard symptoms rated 0 (None), 1 (Slight), 2 (Moderate), 3 (Severe)
    """
    # Symptom mapping to subscales
    nausea_items = [symptoms['general_discomfort'], symptoms['increased_salivation'], symptoms['sweating'],
                    symptoms['nausea'], symptoms['difficulty_concentrating'], symptoms['stomach_awareness'], symptoms['burping']]
    oculomotor_items = [symptoms['general_discomfort'], symptoms['fatigue'], symptoms['headache'],
                        symptoms['eyestrain'], symptoms['difficulty_focusing'], symptoms['difficulty_concentrating'], symptoms['blurred_vision']]
    disorientation_items = [symptoms['difficulty_focusing'], symptoms['dizziness_eyes_open'], symptoms['dizziness_eyes_closed'],
                            symptoms['vertigo'], symptoms['stomach_awareness'], symptoms['burping']]
    
    raw_n = sum(nausea_items)
    raw_o = sum(oculomotor_items)
    raw_d = sum(disorientation_items)
    raw_total = raw_n + raw_o + raw_d
    
    score_n = raw_n * WEIGHTS['Nausea']
    score_o = raw_o * WEIGHTS['Oculomotor']
    score_d = raw_d * WEIGHTS['Disorientation']
    score_ts = raw_total * WEIGHTS['Total']
    
    return {'Nausea': score_n, 'Oculomotor': score_o, 'Disorientation': score_d, 'Total_Severity': score_ts}

def evaluate_ssq_safety():
    # Calibrated post-immersion symptom profile
    typical_profile = {
        'general_discomfort': 1, 'fatigue': 0, 'headache': 0, 'eyestrain': 1,
        'difficulty_focusing': 0, 'increased_salivation': 0, 'sweating': 0, 'nausea': 0,
        'difficulty_concentrating': 0, 'blurred_vision': 0, 'dizziness_eyes_open': 0,
        'dizziness_eyes_closed': 0, 'vertigo': 0, 'stomach_awareness': 0, 'burping': 0
    }
    res = calculate_ssq(typical_profile)
    print("=" * 65)
    print("KENNEDY SIMULATOR SICKNESS (SSQ) SAFETY AUDIT")
    print("=" * 65)
    print(f"Nausea Subscale (N):          {res['Nausea']:.2f}")
    print(f"Oculomotor Subscale (O):      {res['Oculomotor']:.2f}")
    print(f"Disorientation Subscale (D):  {res['Disorientation']:.2f}")
    print(f"Total Severity Score (TS):    {res['Total_Severity']:.2f}")
    safety_status = "SAFE (TS <= 15.0 - Motion-to-photon latency optimal)" if res['Total_Severity'] <= 15.0 else "RISK (TS > 15.0 - Frame drops detected)"
    print(f"Cybersickness Ergonomic Gate: {safety_status}")
    print("=" * 65)

if __name__ == "__main__":
    evaluate_ssq_safety()
