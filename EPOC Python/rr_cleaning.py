import numpy as np
import pandas as pd
import neurokit2 as nk
import argparse
import sys
import os
from scipy.signal import butter, filtfilt, iirnotch

def butter_highpass(data, cutoff, fs, order=5):
    """
    Apply a high-pass Butterworth filter to remove baseline wander.
    """
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    y = filtfilt(b, a, data)
    return y

def butter_lowpass(data, cutoff, fs, order=5):
    """
    Apply a low-pass Butterworth filter to remove high-frequency noise.
    """
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

def iir_notch(data, cutoff, fs, Q=30):
    """
    Apply a notch filter to remove power line interference (50/60Hz).
    """
    nyq = 0.5 * fs
    w0 = cutoff / nyq
    b, a = iirnotch(w0, Q)
    y = filtfilt(b, a, data)
    return y


def clean_rr_intervals(rr_intervals, min_rr=600, max_rr=2000):
    """
    Cleans R-R intervals using NeuroKit2's artifact correction and Pandas.

    Args:
        rr_intervals (list or np.array): List of R-R intervals in milliseconds.
        min_rr (float): Minimum acceptable R-R interval (default 300ms).
        max_rr (float): Maximum acceptable R-R interval (default 2000ms).

    Returns:
        pd.Series: Cleaned R-R intervals.
    """
    # Convert to pandas Series
    rr = pd.Series(rr_intervals)
    
    # 1. Simple Range Filtering using Pandas
    # Replace outliers with NaNs or just filter them. 
    # NeuroKit's fixpeaks is better at correcting, but initial range filtering is improved by just dropping obvious noise.
    # However, to preserve the timeline for fixpeaks, let's keep them but mark them?
    # Actually, let's let fixpeaks handle artifacts if possible, or filter strict outliers first.
    # Let's do a strict physical filter first since 100ms or 5000ms are definitely noise.
    rr_physio = rr[(rr >= min_rr) & (rr <= max_rr)]
    
    if rr_physio.empty:
        return pd.Series([], dtype=float)

    # Re-index is not needed if we are just creating a new timeline, but we want to flow.
    # If we dropped values, the continuity is broken.
    # For HRV, continuity matters.
    # If we have big gaps, we might treat them as segments.
    # But for this simple script, let's treat the filtered list as the input stream (assuming dropped beats are just noise).
    
    rr_values = rr_physio.values
    
    # 2. NeuroKit2 Artifact Correction
    # fixpeaks works on specific peak locations. We need to reconstruct peaks.
    # We assume RR intervals are in ms. We treat them as samples (1000Hz sampling rate).
    # Peaks = cumulative sum.
    # We prepend 0 to represent the start time, ensuring the first interval is preserved after diff.
    peaks = np.concatenate(([0], np.cumsum(rr_values)))
    
    try:
        # sampling_rate=1000 because our "unit" is ms.
        result = nk.signal_fixpeaks(peaks, sampling_rate=1000, method="neurokit")
        
        # signal_fixpeaks can return (info, peaks) or (peaks, info) depending on version/context?
        # Based on debug, it returned (dict, array).
        if isinstance(result, tuple):
            if isinstance(result[0], dict):
                cleaned_peaks = result[1]
            else:
                cleaned_peaks = result[0]
        else:
            cleaned_peaks = result
            
        cleaned_peaks = np.array(cleaned_peaks)
        
        # We need to convert back to intervals.
        cleaned_rr = np.diff(cleaned_peaks)
        
        # Handle if cleaned_rr has NaNs
        cleaned_rr = cleaned_rr[~np.isnan(cleaned_rr)]
        
        return pd.Series(cleaned_rr)
        
    except Exception as e:
        print(f"NeuroKit adjustment failed: {e}. Returning range-filtered data.")
        # import traceback
        # traceback.print_exc()
        return pd.Series(rr_values)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean R-R intervals from ECG data.')
    parser.add_argument('file', nargs='?', help='Path to the input file containing R-R intervals (CSV or text, one column).')
    
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
            
        try:
            # Try reading as CSV, assuming no header if it's just numbers
            # If it has a header, pandas usually detects it, but for single column numbers it might treat first row as header.
            # Let's try to sniff or just assume header=None for simplicity given the user prompt context "file with data".
            # Safest is header=None for raw numbers.
            df = pd.read_csv(args.file, header=None)
            
            # Assuming the first column is the data
            data = df.iloc[:, 0].tolist()
            print(f"Loaded {len(data)} intervals from '{args.file}'.")
            
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    else:
        # Sample data with noise
        data = [800, 810, 790, 100, 805, 5000, 800, 1200, 820, 815, 600, 6000, 600]
        print("No file provided. Using sample data.")
        print(f"Original Data: {data}")

    cleaned_data = clean_rr_intervals(data)
    
    print("\nCleaned Data:")
    # Print as list or just values
    print(cleaned_data.values)
    
    print(f"\nOriginal count: {len(data)}")
    print(f"Cleaned count: {len(cleaned_data)}")
