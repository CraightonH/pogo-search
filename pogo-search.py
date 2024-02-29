import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import yaml
import logging
from sys import exit as sys_exit
import os

log = logging.getLogger("pogo.py")

config = {}

def appSetup():
  """
  Sets up config and logging
  """
  log_level_opt = {
      "debug": logging.DEBUG,
      "info": logging.INFO,
      "warning": logging.WARNING,
      "warn": logging.WARNING,
      "error": logging.ERROR,
      "critical": logging.CRITICAL
  }
  try:
      config_dir = 'config'
      if os.getenv("CONFIG_DIRECTORY_NAME") is not None:
          config_dir = os.environ["CONFIG_DIRECTORY_NAME"]
      for file in os.listdir(config_dir):
          if os.path.isfile(os.path.join(config_dir, file)):
              with open(f'{config_dir}/{file}', 'r', encoding="utf-8") as config_stream:
                  config.update(yaml.safe_load(config_stream))
  except FileNotFoundError:
      # pylint: disable=C0301
      print("Could not find config file. Please review documentation on config file location/format.")
      sys_exit(1)

  log.setLevel(log_level_opt[config["logging"]["level"].lower()])
  logHandle = logging.StreamHandler()
  logHandle.setLevel(log_level_opt[config["logging"]["level"].lower()])
  logHandle.setFormatter(logging.Formatter(config["logging"]["format"]))
  log.addHandler(logHandle)

def buildRangeNames(sheetName, rangeConfig):
  result = []
  rangeTemplate = "'{}'!{}{}:{}{}"
  for rangeType in rangeConfig:
    result.append(rangeTemplate.format(sheetName, rangeType['range']['startCol'], rangeType['range']['startRow'], rangeType['range']['endCol'], rangeType['range']['endRow']))
  return result

def batchGetValues(spreadsheetId, rangeNames):
  log.info("Acquiring pokemon data")
  creds, _ = google.auth.default()
  try:
    service = build("sheets", "v4", credentials=creds)
    result = (
        service.spreadsheets()
        .values()
        .batchGet(spreadsheetId=spreadsheetId, ranges=rangeNames)
        .execute()
    )
    ranges = result.get("valueRanges", [])
    # log.debug(f"retrieved ranges: {result}")
    return result
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

def isShadow(pokemonName):
  for shadow in config['shadows']:
    return (shadow['findFromData'].lower() in pokemonName.lower())

def isTransform(pokemonName):
  transformationFound = False
  for transformation in config['transforms']:
    transformationFound = transformation.lower() in pokemonName.lower()
    if transformationFound:
      return transformationFound
  return transformationFound

def getRegion(pokemonName):
  for region in config['regions']:
    if "shorthand" in config['regions'][region]:
      if config['regions'][region]['shorthand'].lower() in pokemonName.lower():
        return region
    if config['regions'][region]['demonym'].lower() in pokemonName.lower():
      return region
  return False

def cleanPokemonTier(tier):
  cleanTier = tier
  for substr in config['tier']['remove']:
    cleanTier = cleanTier.replace(substr, '')
  return cleanTier

def cleanPokemonName(pokemonObj, pokemonName):
  cleanName = pokemonName.lower()
  if pokemonObj['shadow']:
    for substr in config['shadows']:
      cleanName = cleanName.replace(substr['findFromData'].lower(), '')
  if pokemonObj['transform']:
    for substr in config['transforms']:
      cleanName = cleanName.replace(substr.lower(), '')
  if pokemonObj['region']:
    for key in config['regions'][pokemonObj['region']]:
      substr = config['regions'][pokemonObj['region']][key].lower()
      if pokemonObj['shadow']:
        substr = substr.lstrip()
      cleanName = cleanName.replace(substr, '')
  return cleanName.strip()

def buildPokemonObject(pokemonRange):
  pokemonObj = {}
  pokemonName = pokemonRange[0]
  pokemonObj['tier'] = cleanPokemonTier(pokemonRange[len(pokemonRange) - 1])
  pokemonObj['shadow'] = isShadow(pokemonName)
  pokemonObj['transform'] = isTransform(pokemonName)
  pokemonObj['region'] = getRegion(pokemonName)
  pokemonObj['name'] = cleanPokemonName(pokemonObj, pokemonName)
  return pokemonObj

def getTopPvePokemon():
  log.info("Getting Top PvE Pokemon Data")
  pokemon = {}
  pokemon['types'] = {}
  pokemon['tiers'] = {"S": [], "A": [], "B": [], "C": [], "D": [], "E": [], "F": []}
  spreadsheetId = config['spreadsheetId']
  sheetId = "pve"
  batchResults = batchGetValues(spreadsheetId, buildRangeNames(config['sheets'][sheetId]['name'], config['sheets'][sheetId]['ranges']))
  valueRanges = batchResults['valueRanges']
  log.info("Parsing results")
  for index in range(len(config['sheets'][sheetId]['ranges'])):
    pokemon['types'][config['sheets'][sheetId]['ranges'][index]['type']] = []
    for pokemonRange in valueRanges[index]['values']:
      pokemonObj = buildPokemonObject(pokemonRange)
      pokemon['tiers'][pokemonObj['tier']].append(pokemonObj)
      pokemon['types'][config['sheets'][sheetId]['ranges'][index]['type']].append(pokemonObj)
  return pokemon

def getRaidCounters():
  # assume most damage is from shadow/mega forms, so don't track the differences 
  log.info("Getting Raid Counter Pokemon Data")
  pokemon = {"boss": set(), "counters": set()}
  spreadsheetId = config['spreadsheetId']
  sheetId = "raid"
  batchResults = batchGetValues(spreadsheetId, buildRangeNames(config['sheets'][sheetId]['name'], config['sheets'][sheetId]['ranges']))
  valueRanges = batchResults['valueRanges']
  log.info("Parsing results")
  for index in range(len(config['sheets'][sheetId]['ranges'])):
    rangeName = config['sheets'][sheetId]['ranges'][index]['name']
    for pokemonRange in valueRanges[index]['values']:
      for pokemonName in pokemonRange:
        pokemon[rangeName].add(pokemonName.replace('Mega ', '').strip())
  return pokemon

def buildTierQueryStrings(tiers):
  log.info("Building query strings for pokemon tiers")
  queryStrings = {}
  for tier in tiers:
    queryStrings[tier] = ""
    queryStrings[tier] = buildQueryString(tiers[tier])
  return queryStrings

def buildTypeQueryStrings(types):
  log.info("Building query strings for pokemon types")
  queryStrings = {}
  for pType in types:
    queryStrings[pType] = ""
    queryStrings[pType] = buildQueryString(types[pType])
  return queryStrings

def buildRaidCounterQueryString(pokemonSet):
  log.info("Building raid counter query string")
  allPokemonQueryStr = ""
  for pokemon in pokemonSet:
    allPokemonQueryStr = allPokemonQueryStr + f"{config['search']['family']}{pokemon}{config['search']['also']}"
  return allPokemonQueryStr[:-1]

def buildQueryString(pokemonList):
  allPokemonQueryStr = ""
  shadowQueryStr = ""
  nonShadowQueryStr = ""
  regionQueryStr = ""
  wholeQueryStr = ""
  shadows = set()
  nonShadowsOnly = set()
  for pokemon in pokemonList:
    # log.debug(f"pokemon: {pokemon}")
    if pokemon['shadow']:
      shadows.add((pokemon['name'], pokemon['region']))
    else:
      nonShadowsOnly.add((pokemon['name'], pokemon['region']))
  shadowsOnly = shadows.difference(nonShadowsOnly)
  both = shadows.intersection(nonShadowsOnly)
  nonShadowsOnly.difference_update(both)
  # log.debug(f"shadowsOnly: {shadowsOnly}")
  # log.debug(f"nonShadowsOnly: {nonShadowsOnly}")
  # log.debug(f"both: {both}")
  for pokemon in both:
    allPokemonQueryStr = allPokemonQueryStr + f"{config['search']['family']}{pokemon[0]}{config['search']['also']}"
    if pokemon[1]:
      regionQueryStr = regionQueryStr + f"{config['search']['and']}{config['search']['not']}{config['search']['family']}{pokemon[0]}{config['search']['also']}{pokemon[1]}"
  for pokemon in nonShadowsOnly:
    allPokemonQueryStr = allPokemonQueryStr + f"{config['search']['family']}{pokemon[0]}{config['search']['also']}"
    if pokemon[1]:
      regionQueryStr = regionQueryStr + f"{config['search']['and']}{config['search']['not']}{config['search']['family']}{pokemon[0]}{config['search']['also']}{pokemon[1]}"
    nonShadowQueryStr = nonShadowQueryStr + f"{config['search']['and']}{config['search']['not']}{config['search']['family']}{pokemon[0]}{config['search']['also']}{config['search']['not']}{config['search']['shadow']}"
  for pokemon in shadowsOnly:
    allPokemonQueryStr = allPokemonQueryStr + f"{config['search']['family']}{pokemon[0]}{config['search']['also']}"
    if pokemon[1]:
      regionQueryStr = regionQueryStr + f"{config['search']['and']}{config['search']['not']}{config['search']['family']}{pokemon[0]}{config['search']['also']}{pokemon[1]}"
    shadowQueryStr = shadowQueryStr + f"{config['search']['and']}{config['search']['not']}{config['search']['family']}{pokemon[0]}{config['search']['also']}{config['search']['shadow']}"
  allPokemonQueryStr = allPokemonQueryStr[:-1]
  wholeQueryStr = allPokemonQueryStr + nonShadowQueryStr + shadowQueryStr + regionQueryStr
  # log.debug(f"queryStr: {allPokemonQueryStr}")
  # log.debug(f"nonShadowQueryStr: {nonShadowQueryStr}")
  # log.debug(f"shadowQueryStr: {shadowQueryStr}")
  # log.debug(f"regionQueryStr: {regionQueryStr}")
  # log.debug(f"wholeQueryStr: {wholeQueryStr}")
  return wholeQueryStr

def writeQueryToFile(filePath, query):
  log.info(f"Writing data to {config['output']['folder']}/{filePath}")
  with open(f"{config['output']['folder']}/{filePath}", 'w') as f:
    f.write(query)

if __name__ == "__main__":
  appSetup()

  pvePokemon = getTopPvePokemon()
  tierQueryStrings = buildTierQueryStrings(pvePokemon['tiers'])
  # log.debug(f"tierQueryStrings: {tierQueryStrings}")
  combinedTierQueryStrings = f"{tierQueryStrings['S']}"
  for tier in tierQueryStrings:
    writeQueryToFile(f"pve/tiers/{tier}tier.txt", tierQueryStrings[tier])
    if tier != "S":
      combinedTierQueryStrings = ",".join([combinedTierQueryStrings, tierQueryStrings[tier]])
      writeQueryToFile(f"pve/keep/S-{tier}tier.txt", combinedTierQueryStrings)

  typeQueryStrings = buildTypeQueryStrings(pvePokemon['types'])
  # log.debug(f"typeQueryStrings: {typeQueryStrings}")
  for pType in typeQueryStrings:
    writeQueryToFile(f"pve/types/{pType}.txt", typeQueryStrings[pType])

  raidCounterPokemon = getRaidCounters()
  raidCounterQueryString = buildRaidCounterQueryString(raidCounterPokemon['counters'])
  writeQueryToFile(f"pve/raid/{raidCounterPokemon['boss'].pop()}.txt", raidCounterQueryString)
  writeQueryToFile(f"pve/raid/000_ThisWeek.txt", raidCounterQueryString)
