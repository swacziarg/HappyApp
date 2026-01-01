## Garmin Raw Inventory

### Sleep - DI-Connect-Wellness
- *_sleepData.json
  - calendarDate
  - sleepStartTimestampGMT
  - sleepEndTimestampGMT
  - deepSleepSeconds
  - lightSleepSeconds
  - remSleepSeconds
  - awakeSleepSeconds
  - sleepScores.overallScore

### Health Status - DI-Connect-Wellness
- *_healthStatusData.json
  - calendarDate
  - metrics[type=HRV, HR, RESPIRATION, SKIN_TEMP_C]

### Daily Summary (UDS) - DI-Connect-Aggregator
- UDSFile_*.json
  - totalSteps
  - totalKilocalories
  - allDayStress.aggregatorList
  - bodyBattery.statList
