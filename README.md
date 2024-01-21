# PoGo Search Strings
Data collected from [PoGo Raid & Info Sheets](https://docs.google.com/spreadsheets/d/1avftwmBHszB0s1_5-Z_REvvAMXdLk0vMJI3GYsSWGkg/edit#gid=318359852). According to the author, data will be updated around once per week.

If there is a high-tier non-shadow pokemon, it almost always needs to be a Mega pokemon to qualify for the tier. 

### Queries
The `queries` folder contains all of the generated queries based on the data collected.

As of now, the queries do not sort pokemon alphabetically and order is not guaranteed, so it's likely that the queries will change.

### Running yourself
Before this will work, you need to follow instructions for setting up [Google ADC](https://cloud.google.com/docs/authentication/provide-credentials-adc#local-dev) so you can access Google APIs. 

**Note:** Free-tier usage includes up to 60 Google Sheets API calls per minute and `pogo-search` will run an estimated 4 queries per run.
