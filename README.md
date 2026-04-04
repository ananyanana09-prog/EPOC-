# EPOC
A wearable-based system that estimates Excess Post-Exercise Oxygen Consumption (EPOC) using multi-sensor physiological data (HR, HRV, respiration, skin temperature, and motion) to improve accuracy beyond traditional heart rate–only models.
This project builds a low-cost, multi-sensor model to estimate Excess Post-Exercise Oxygen Consumption (EPOC)—the extra oxygen your body uses after exercise to recover. EPOC reflects workout intensity, oxygen debt, and how much energy your body needs to return to its resting state.

Most existing systems estimate EPOC using only heart rate data and proprietary algorithms. This project expands on that approach by integrating multiple physiological signals to create a more accurate and transparent model.

What is EPOC?

EPOC is the increased oxygen consumption that occurs after exercise as the body works to restore normal conditions. It is highest after intense or anaerobic workouts like sprinting or weightlifting.

The body uses this extra oxygen to:

Restore ATP (energy stores)
Remove and process lactic acid
Repair muscle tissue
Regulate body temperature

This process is also known as the afterburn effect, where metabolism stays elevated even after exercise ends.

Key Physiological Signals

Heart Rate (HR)

Indicates exercise intensity
Higher HR → greater oxygen demand → higher EPOC

Heart Rate Variability (HRV)

Includes SDNN, RMSSD, and pNN50
Reflects autonomic nervous system activity
Lower HRV during recovery → higher stress and oxygen demand

R-R Intervals

Time between heartbeats (from ECG)
Short intervals = high intensity (sympathetic activity)
Long intervals = recovery (parasympathetic activity)
Recovery speed reflects EPOC

Respiration Rate

Direct measure of oxygen intake and demand
Helps better estimate oxygen repayment

Skin Temperature

Reflects thermoregulation during recovery
Cooling requires energy, contributing to EPOC

Motion (Accelerometer Data)

Detects movement artifacts
Improves data quality and reduces false signals
Hypothesis

A model that combines HR, HRV, respiration, skin temperature, and motion will estimate EPOC more accurately than models using only HR and HRV.

Expected Outcomes
~10% improvement in EPOC estimation accuracy
Better modeling of recovery using temperature data
Reduced noise and false spikes using motion tracking
More reliable and personalized fitness insights
⚙️ Methodology

1. Data Collection
Wearable device records:

HR and R-R intervals
HRV metrics (SDNN, RMSSD, pNN50)
Motion (3-axis accelerometer)

2. Data Preprocessing

Filter noise (moving average / low-pass filtering)
Handle missing or corrupted data
Normalize signals using baseline values

3. Epoch Segmentation

Split data into 1-minute intervals
Enables time-based recovery analysis

4. Feature Extraction (per epoch)

Mean HR
Mean R-R interval
HRV metrics
Motion magnitude

5. EPOC Estimation

Track recovery trends across epochs
Estimate oxygen consumption over time
Sum epoch values for total EPOC
