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
    log.debug(f"{len(ranges)} ranges retrieved")
    log.debug(f"retrieved ranges: {result}")
    return result
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

def getTopPvePokemon():
  log.debug("Beginning getTopPvePokemon")
  spreadsheetId = config['spreadsheetId']
  sheetId = "pve"
  log.debug(f"spreadsheetId: {spreadsheetId}, sheetId: {sheetId}")
  pokemon = batchGetValues(spreadsheetId, buildRangeNames(config['sheets'][sheetId]['name'], config['sheets'][sheetId]['ranges']))
  return pokemon
  # for index in range(len(config['sheets']['pveTop']['ranges'])):
    
# pokemon:
#   bug:
#     - name: Mega Heracross
#       tier: S-
#       isShadow: false

if __name__ == "__main__":
  appSetup()

  pvePokemon = getTopPvePokemon()
