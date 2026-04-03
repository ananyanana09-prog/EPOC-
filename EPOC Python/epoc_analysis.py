import numpy as np
import pandas as pd
import neurokit2 as nk
import argparse
import sys
import os
from rr_cleaning import clean_rr_intervals

def calculate_hr_features(rr_intervals):
    """
    Calculates Heart Rate (HR) and HR_sum from R-R intervals.
    
    Args:
        rr_intervals (pd.Series or np.array): R-R intervals in milliseconds.
        
    Returns:
        tuple: (mean_hr, hr_sum, hr_values)
    """
    # Convert RR (ms) to HR (bpm)
    # HR = 60000 / RR_ms
    hr_values = 60000 / rr_intervals
    
    mean_hr = np.mean(hr_values)
    hr_sum = np.sum(hr_values)
    
    return mean_hr, hr_sum, hr_values

def get_hrv_metrics(rr_intervals):
    """
    Extracts RMSSD, SDNN, and pNN50 using manual formulas.
    
    Args:
        rr_intervals (pd.Series or np.array): Cleaned R-R intervals in ms.
        
    Returns:
        pd.DataFrame: DataFrame containing the HRV metrics.
    """
    if len(rr_intervals) < 2:
        return pd.DataFrame()

    rr = np.array(rr_intervals)
    diff_rr = np.diff(rr)
    
    # User provided formulas:
    # SDNN = np.std(rr_intervals)
    # RMSSD = np.sqrt(np.mean(np.diff(rr_intervals)**2))
    # NN50 = np.sum(np.abs(np.diff(rr_intervals)) > 50)
    # pNN50 = NN50 / (len(rr_intervals) - 1) * 100
    sdnn = np.std(rr)
    rmssd = np.sqrt(np.mean(diff_rr**2))
    nn50 = np.sum(np.abs(diff_rr) > 50)
    
    # Denominator for pNN50 is number of differences, which is len(rr) - 1
    if len(diff_rr) > 0:
        pnn50 = (nn50 / len(diff_rr)) * 100
    else:
        pnn50 = 0.0
        
    features = pd.DataFrame({
        'HRV_RMSSD': [rmssd], 
        'HRV_SDNN': [sdnn], 
        'HRV_pNN50': [pnn50]
    })
    return features

# Regression Equations
def epoc_cex(ffm, hr_sum):
    """EPOC for Continuous Exercise (kcal)"""
    return -37.128 + (1.003 * ffm) + (0.016 * hr_sum)

def epoc_iex(ffm, hr_sum):
    """EPOC for Interval Exercise (kcal)"""
    return -49.265 + (1.442 * ffm) + (0.013 * hr_sum)

def epoc_aex(ffm, hr_sum):
    """EPOC for Accumulated Exercise (kcal)"""
    return -100.942 + (2.209 * ffm) + (0.020 * hr_sum)

def validate_epoc_vo2(time_min, vo2_vals, resting_vo2):
    """
    Calculates EPOC from VO2 data using trapezoidal integration.
    EPOC (L or kcal? Usually L O2, convert to kcal ~5 kcal/L)
    Here we calculate the integral of (VO2 - Resting) dt.
    
    Args:
        time_min (list/array): Time points in minutes.
        vo2_vals (list/array): VO2 values (e.g., L/min or ml/kg/min). 
                               Units must be consistent. Assuming L/min for absolute EPOC.
        resting_vo2 (float): Resting VO2 value (same units).
        
    Returns:
        float: EPOC volume (integral).
    """
    # Filter for values > resting_vo2 (only "excess" counts)
    y_vals = np.array(vo2_vals) - resting_vo2
    y_vals[y_vals < 0] = 0
    
    # Integrate using trapezoidal rule
    epoc_integral = np.trapz(y_vals, x=time_min)
    return epoc_integral

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Estimate EPOC from R-R intervals and FFM.')
    parser.add_argument('file', nargs='?', help='Path to the input file containing R-R intervals (CSV/Text).')
    parser.add_argument('--ffm', type=float, help='Fat-Free Mass (kg).')
    parser.add_argument('--type', choices=['CEx', 'IEx', 'AEx'], help='Exercise Type: CEx (Continuous), IEx (Interval), AEx (Accumulated).')
    parser.add_argument('--start', type=int, default=0, help='Start index for exercise phase (default 0).')
    parser.add_argument('--end', type=int, default=None, help='End index for exercise phase (default End).')

    args = parser.parse_args()

    # Default Logic / Demo Mode
    if args.file is None:
        print("No input file provided. Running in DEMO MODE.")
        print("Usage: python epoc_analysis.py <file> --ffm <val> --type <type>")
        print("Using default: test_data.csv --ffm 50 --type CEx\n")
        args.file = 'test_data.csv'
        if args.ffm is None: args.ffm = 50.0
        if args.type is None: args.type = 'CEx'
    else:
        # File provided. Check other required args.
        if args.ffm is None:
            print("Warning: --ffm not provided. Using default 50kg (approx. teen/avg adult).")
            args.ffm = 50.0
        if args.type is None:
            print("Warning: --type not provided. Using default CEx.")
            args.type = 'CEx'

    # Load Data
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    try:
        df = pd.read_csv(args.file, header=None)
        raw_rr = df.iloc[:, 0].values
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    print(f"Loaded {len(raw_rr)} intervals.")

    # Auto-detect units (Seconds vs Milliseconds)
    mean_rr = np.mean(raw_rr)

    if mean_rr < 10:
        # seconds (0.6–1.5 typical)
        raw_rr = raw_rr * 1000
        print("Detected input in seconds. Converting to milliseconds.")
    elif mean_rr >= 10 and mean_rr < 3000:
        # milliseconds (600–1200 typical)
        print("Detected input in milliseconds.")
    else:
        raise ValueError("RR interval values out of physiological range.")

    # 1. Cleaning
    clean_rr = clean_rr_intervals(raw_rr)
    print(f"Cleaned data count: {len(clean_rr)}")
    
    if len(clean_rr) == 0:
        print("Error: No data remaining after cleaning.")
        sys.exit(1)

    # 2. Define Exercise Phase (on CLEANED or RAW? Usually indices refer to original time, 
    # but after cleaning indices shift. 
    # For HR_sum "during exercise", we usually apply to the cleaned sequence corresponding to that phase.
    # If the user gives indices, they likely refer to the file lines.
    # Simple approach: Slice RAW first, then CLEAN.
    end_idx = args.end if args.end is not None else len(raw_rr)
    exercise_rr_raw = raw_rr[args.start:end_idx]
    
    # Clean the specific phase
    exercise_rr_clean = clean_rr_intervals(exercise_rr_raw)
    
    # 3. Calculate HR Features
    mean_hr, hr_sum, _ = calculate_hr_features(exercise_rr_clean)
    
    print(f"Exercise Phase: Indices {args.start}-{end_idx}")
    print(f"Mean HR: {mean_hr:.2f} bpm")
    print(f"HR Sum: {hr_sum:.2f}")

    # 4. Extract HRV Features (Recovery correlation)
    hrv_metrics = get_hrv_metrics(exercise_rr_clean)
    print("\nHRV Metrics:")
    print(hrv_metrics.to_string(index=False))

    # 5. Estimate EPOC
    epoc_est = 0.0
    if args.type == 'CEx':
        epoc_est = epoc_cex(args.ffm, hr_sum)
    elif args.type == 'IEx':
        epoc_est = epoc_iex(args.ffm, hr_sum)
    elif args.type == 'AEx':
        epoc_est = epoc_aex(args.ffm, hr_sum)

    print(f"\nEstimated EPOC ({args.type}): {epoc_est:.2f} kcal")
