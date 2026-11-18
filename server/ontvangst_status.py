"""Lees een consistent overzicht, zonder brokerwachtwoorden of serveradressen."""
import argparse,json
from meetgegevens import overzicht

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database',default='/var/lib/iot/verzamelde_metingen.db')
    a=p.parse_args()
    print(json.dumps(overzicht(a.database),ensure_ascii=False,indent=2))
