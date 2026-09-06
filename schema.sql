CREATE TABLE IF NOT EXISTS "Company" (
    "internalId" bigserial PRIMARY KEY,
    "bseScriptCode" varchar(15),
    "nseScriptCode" varchar(15),
    "isinCode" varchar(20) UNIQUE,
    "startDate" date,
    "endDate" date,
    "activeStatus" boolean DEFAULT true,
    "lastUpdatedTimeStamp" timestamp DEFAULT CURRENT_TIMESTAMP,
    "scriptType" varchar(5),
    "companyname" varchar(110)
);

CREATE TABLE IF NOT EXISTS public.nse_script_closing_raw_data (
    "internalId" bigserial PRIMARY KEY,
    symbol varchar(15),
    series varchar(15),
    open numeric(10, 2),
    high numeric(10, 2),
    low numeric(10, 2),
    close numeric(10, 2),
    "prevClose" numeric(10, 2),
    "totalTradeQty" bigint,
    "totalTradeValue" numeric(20, 2),
    "tradeDate" date,
    "totalTrades" integer,
    isin varchar(20),
    "lastUpdatedTimeStamp" timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.nse_script_closing_prs_data (
    "internalId" bigserial PRIMARY KEY,
    "companyIntId" bigint REFERENCES "Company"("internalId"),
    open numeric(10, 2),
    high numeric(10, 2),
    low numeric(10, 2),
    close numeric(10, 2),
    "prevClose" numeric(10, 2),
    "totalTradeQty" bigint,
    "totalTradeValue" numeric(20, 2),
    "tradeDate" date,
    "totalTrades" integer,
    "lastUpdatedTimeStamp" timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.users (
    emailid varchar(75) PRIMARY KEY,
    name varchar(40),
    password varchar(120)
);