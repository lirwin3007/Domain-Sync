import requests
import configparser
from datetime import datetime

config = None

def readConfig():
    global config
    if config is None:
        config = configparser.ConfigParser()
        config.read('config.ini')
    return config

def log(status, line):
    config = readConfig()
    with open(config['Setup']['logFile'], 'a') as logFile:
        logFile.write(f'{datetime.now()} - [{status}] {line}\n')

def getDomainRecord():
    config = readConfig()
    headers = {"Authorization": f"Bearer {config['Setup']['DOToken']}", "Content-Type": "application/json"}

    r = requests.get(f"https://api.digitalocean.com/v2/domains/{config['Domain']['domain']}/records", headers=headers)
    if r.status_code != 200:
        log('Error', f"https://api.digitalocean.com/v2/domains/{config['Domain']['domain']}/records resulted in status code {r.status_code}")
        exit(1)

    results = r.json()['domain_records']
    results = list(filter(lambda x: x['type'] == 'A' and x['name'] == config['Domain']['hostname'], results))

    if len(results) == 0:
        log('Error', f"No entry for {config['Domain']['hostname']} found")
        exit(1)

    if len(results) > 1:
        log('Warning', f"Multiple entries for {config['Domain']['hostname']} found - using first")

    domainRecord = results[0]

    return domainRecord

def changeDomainRecord(domainRecord, newValue):
    config = readConfig()
    headers = {"Authorization": f"Bearer {config['Setup']['DOToken']}", "Content-Type": "application/json"}
    url = f"https://api.digitalocean.com/v2/domains/{config['Domain']['domain']}/records/{domainRecord['id']}"
    payload = {
        'data': newValue,
        'ttl': 30
    }
    r = requests.request("PUT", url, headers=headers, params = payload)
    if r.status_code != 200:
        log('Error', f"https://api.digitalocean.com/v2/domains/{config['Domain']['domain']}/records/{domainRecord['id']} resulted in status code {r.status_code}")
        exit(1)

def main():
    r = requests.get('http://ifconfig.me/ip')

    if r.status_code != 200:
        log('Error', f'Request to http://ifconfig.me/ip resulted in status code {r.status_code}')
        exit(1)

    publicIP = r.text
    domainRecord = getDomainRecord()

    if domainRecord['data'] != publicIP:
        log('Info', f"Change of public IP detected! Changing from {domainRecord['data']} to {publicIP}")
        changeDomainRecord(domainRecord, publicIP)
        log('Info', f"Change succesful! Domain now points to {publicIP}")

if __name__ == "__main__":
    main()