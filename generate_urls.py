import pandas as pd

# The official root domains for all 50 US states
states = {
    "AL": "alabama.gov", "AK": "alaska.gov", "AZ": "az.gov", "AR": "arkansas.gov",
    "CA": "ca.gov", "CO": "colorado.gov", "CT": "ct.gov", "DE": "delaware.gov",
    "FL": "myflorida.com", "GA": "georgia.gov", "HI": "hawaii.gov", "ID": "idaho.gov",
    "IL": "illinois.gov", "IN": "in.gov", "IA": "iowa.gov", "KS": "kansas.gov",
    "KY": "kentucky.gov", "LA": "louisiana.gov", "ME": "maine.gov", "MD": "maryland.gov",
    "MA": "mass.gov", "MI": "michigan.gov", "MN": "mn.gov", "MS": "ms.gov",
    "MO": "mo.gov", "MT": "mt.gov", "NE": "nebraska.gov", "NV": "nv.gov",
    "NH": "nh.gov", "NJ": "nj.gov", "NM": "newmexico.gov", "NY": "ny.gov",
    "NC": "nc.gov", "ND": "nd.gov", "OH": "ohio.gov", "OK": "ok.gov",
    "OR": "oregon.gov", "PA": "pa.gov", "RI": "ri.gov", "SC": "sc.gov",
    "SD": "sd.gov", "TN": "tn.gov", "TX": "texas.gov", "UT": "utah.gov",
    "VT": "vermont.gov", "VA": "virginia.gov", "WA": "wa.gov", "WV": "wv.gov",
    "WI": "wisconsin.gov", "WY": "wyo.gov"
}

# 50 standard state agency subdomains
prefixes = [
    "www.", "governor.", "ag.", "treasury.", "dot.", "dps.", "health.", "revenue.",
    "education.", "dnr.", "sos.", "labor.", "commerce.", "insurance.", "corrections.",
    "agriculture.", "veterans.", "parks.", "lottery.", "emergency.", "housing.",
    "dhs.", "dfs.", "ethics.", "courts.", "gaming.", "tax.", "water.", "wildlife.",
    "energy.", "library.", "museum.", "arts.", "history.", "aging.", "children.",
    "transportation.", "environment.", "forestry.", "military.", "police.", "safety.",
    "healthdepartment.", "budget.", "finance.", "administration.", "personnel.",
    "technology.", "tourism.", "economicdevelopment.", "employment.", "rehabilitation."
]

urls = []
for state, domain in states.items():
    for prefix in prefixes:
        urls.append(f"https://{prefix}{domain}/")

# Generate the CSV
df = pd.DataFrame({"url": urls})
df.to_csv("urls.csv", index=False)
print(f"Generated {len(df)} URLs and saved to urls.csv")