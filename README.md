# PoGo Search Strings
This is a Pokemon Go search string generator using data collected from [PoGo Raid & Info Sheets](https://docs.google.com/spreadsheets/d/1avftwmBHszB0s1_5-Z_REvvAMXdLk0vMJI3GYsSWGkg/edit#gid=318359852). According to the author, data will be updated around once per week.

These are a great starting point for finding good pokemon without having to stay up-to-date on the current meta. The Google Sheet does the work of determining which are good, and this just parses that data into a query you can put into Pokemon Go.

**Note:** It is still helpful to modify the query in Pokemon Go, for example appending `&3*,4*` to find which ones are worth keeping as opposed to which ones are ok to trade or transfer.

## Queries

The `queries` folder contains all of the generated queries based on the data collected.

As of now, the queries do not sort pokemon alphabetically and order is not guaranteed, so it's likely that the queries will change.

If there is a high-tier non-shadow pokemon, it almost always needs to be a Mega pokemon to qualify for the tier. 

### PvE Types

A single pokemon could be returned in multiple type queries because some pokemons' movesets extend beyond their own type. For example, Alakazam, a psychic pokemon, is also in the fighting type group because he can learn a strong fighting move.

### PvE Tiers

A single pokemon could be returned in multiple tier queries for the same reason mentioned above. Alakazam can be found in a high tier query because of its psychic moveset, but also in a low tier query for its off-meta fighting moveset.

### Raid Counters

The raid folder will contain a file for the current raid boss and also a file for each raid boss as a means of historical data. If the same raid boss is featured again in the future, its old file will get overwritten with the newer, presumably better counters.

## Running yourself

Before this will work, you need to follow instructions for setting up [Google ADC](https://cloud.google.com/docs/authentication/provide-credentials-adc#local-dev) so you can access Google APIs. 

**Note:** Free-tier usage includes up to 60 Google Sheets API calls per minute and `pogo-search` will run an estimated 4 queries per run.
