import csv
import os
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from zipfile import ZipFile

import psycopg2
import wget
from bs4 import BeautifulSoup

DB_NAME = os.environ.get("DB_NAME", "stockapp")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "123456")
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "5432")

yesterday = (datetime.now() - timedelta(1)).strftime("%d%b%Y").upper()
y_year = yesterday[5:9]
y_month = yesterday[2:5]

bhav_zip = "cm{}bhav.csv.zip".format(yesterday)
bhav_csv = "cm{}bhav.csv".format(yesterday)
bhav_temp = "cm{}bhav-temp.csv".format(yesterday)
bhav_url = "https://www1.nseindia.com/content/historical/EQUITIES/{}/{}".format(y_year, y_month)


def get_connection():
    return psycopg2.connect(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def company_name_from_isin(isin):
    req = Request(
        "https://www.cdslindia.com/investors/popup-isin.aspx?isin_code={}".format(isin),
        headers={"User-Agent": "XYZ/3.0"},
    )
    webpage = urlopen(req, timeout=20).read()
    a = BeautifulSoup(webpage, features="html.parser")
    webstring = a.prettify()
    pos1 = webstring.find('<span id="lblISIN_Desc">')
    pos2 = webstring.find("</span>", pos1)
    string = webstring[pos1:pos2]
    string = string.removeprefix('<span id="lblISIN_Desc">')
    if "#" in string:
        string = string.split("#", 1)[0]
    elif " - " in string:
        string = string.split(" - ", 1)[0]
    else:
        string = string.split("-", 1)[0]
    string = string.replace("&amp;", "&").strip()
    return string


try:
    print("=============================================================")
    print("LOG")
    print("=============================================================")
    print("Process Started...")
    wget.download("{}/{}{}{}".format(bhav_url, "cm", yesterday, "bhav.csv.zip"))
    print("{} data is being collected now...".format(yesterday))
    with ZipFile(bhav_zip, "r") as zip_object:
        for filename in zip_object.namelist():
            if filename.endswith(".csv"):
                zip_object.extract(filename)
    print(".zip file downloaded from NSE Website...")
    os.remove(bhav_zip)
    with open(bhav_csv, "r") as source:
        reader = csv.reader(source)
        next(reader, None)
        with open(bhav_temp, "w", newline="") as result:
            writer = csv.writer(result)
            for r in reader:
                writer.writerow((r[0], r[1], r[2], r[3], r[4], r[5], r[7], r[8], r[9], r[10], r[11], r[12]))
    os.remove(bhav_csv)
    os.rename(bhav_temp, bhav_csv)
    print(".csv file extracted from .zip file and altered accordingly...")
    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    with open(bhav_csv) as f:
        cursor.copy_from(
            f,
            "nse_script_closing_raw_data",
            columns=("symbol", "series", "open", "high", "low", "close", "prevClose", "totalTradeQty", "totalTradeValue", "tradeDate", "totalTrades", "isin"),
            sep=",",
        )
    conn.commit()
    cursor.execute(
        '''INSERT INTO "Company"("isinCode", "scriptType", "nseScriptCode")
           SELECT isin AS "isinCode", series AS "scriptType", symbol AS "nseScriptCode"
           FROM nse_script_closing_raw_data
           ON CONFLICT("isinCode") DO NOTHING;'''
    )
    conn.commit()
    print("nse_script_closing_raw_data table updated successfully...")
    isin_codes = []
    with open(bhav_csv) as source:
        for row in csv.reader(source):
            isin_codes.append(row[11].strip())
    count, prev = 0, 0
    print("Browsing internet to obtain company names using ISIN code...")
    print("This process may take 30 to 45 minutes. Please be patient...")
    for line in isin_codes:
        try:
            count += 1
            string = company_name_from_isin(line)
            cursor.execute(
                '''UPDATE "Company" SET "companyname" = %s WHERE "Company"."isinCode" LIKE %s;''',
                (string, line),
            )
            if (int((count / len(isin_codes)) * 100)) % 10 == 0 and prev != int((count / len(isin_codes)) * 100):
                print("--> {}/{} - {}% company names obtained by browsing...".format(count, len(isin_codes), int((count / len(isin_codes)) * 100)))
                prev = int((count / len(isin_codes)) * 100)
            conn.commit()
        except Exception:
            pass
    print("Company table updated successfully...")
    cursor.execute(
        '''INSERT INTO nse_script_closing_prs_data("companyIntId", open, high, low, close, "prevClose", "totalTradeQty", "totalTradeValue", "tradeDate", "totalTrades")
           SELECT "companyIntId", open, high, low, close, "prevClose", "totalTradeQty", "totalTradeValue", "tradeDate", "totalTrades"
           FROM (SELECT open, high, low, close, "prevClose", "totalTradeQty", "totalTradeValue", "tradeDate", "totalTrades", "Company"."internalId" as "companyIntId"
                 FROM nse_script_closing_raw_data
                 FULL OUTER JOIN "Company"
                 ON (nse_script_closing_raw_data.isin = "Company"."isinCode")
                 WHERE EXTRACT(DAY FROM nse_script_closing_raw_data."tradeDate") = %s
                   AND to_char(nse_script_closing_raw_data."tradeDate", 'MON') = %s
                   AND EXTRACT(YEAR FROM nse_script_closing_raw_data."tradeDate") = %s) AS TEMP;''',
        (int(yesterday[0:2]), yesterday[2:5], int(yesterday[5:9])),
    )
    conn.commit()
    print("nse_script_closing_prs_data table updated successfully...")
    conn.close()
    os.remove(bhav_csv)
except Exception:
    print("It seems {} was a holiday or a non-working day.".format(yesterday))
    pass
finally:
    print("Process Ended...")
    print("=============================================================")