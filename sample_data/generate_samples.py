import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(SAMPLE_DIR, exist_ok=True)

def create_sample_1_standard():
    """
    Sample 1: Clean, well-structured headers (baseline test).
    Headers in row 1, clean standard naming.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SOV_Schedule"

    headers = [
        "Reference", "Address", "City", "State", "Zip", "County", "Country",
        "Building Value", "Contents", "BI", "Occupancy", "Construction",
        "Storeys", "Number of Buildings", "Year Built", "Fire Sprinklers (Y/N)", "Other"
    ]
    ws.append(headers)

    data = [
        ["LOC-001", "100 California St", "San Francisco", "CA", 94111, "San Francisco", "USA", 12500000.0, 1500000.0, 750000.0, "Commercial Office", "Steel", 12, 1, 2012, "Y", 100000.0],
        ["LOC-002", "550 South Hope St", "Los Angeles", "CA", 90071, "Los Angeles", "USA", 8400000.0, 950000.0, 420000.0, "Retail Center", "Reinforced Concrete", 3, 2, 2015, "Y13", 50000.0],
        ["LOC-003", "1200 6th Ave", "Seattle", "WA", 98101, "King", "USA", 18900000.0, 3200000.0, 1100000.0, "Mixed Use", "Concrete", 18, 1, 2018, "Y", 250000.0],
        ["LOC-004", "700 Louisiana St", "Houston", "TX", 77002, "Harris", "USA", 15200000.0, 2100000.0, 900000.0, "Corporate HQ", "Steel", 24, 1, 2008, "Y", 0.0],
        ["LOC-005", "100 N Riverside Plaza", "Chicago", "IL", 60606, "Cook", "USA", 22000000.0, 4500000.0, 1500000.0, "Office Tower", "Steel Frame", 36, 1, 2001, "Y(13R)", 300000.0],
        ["LOC-006", "300 S Tryon St", "Charlotte", "NC", 28202, "Mecklenburg", "USA", 9800000.0, 1200000.0, 600000.0, "Banking Facility", "Masonry", 8, 1, 2016, "Y", 80000.0],
        ["LOC-007", "400 Capitol Mall", "Sacramento", "CA", 95814, "Sacramento", "USA", 6700000.0, 800000.0, 350000.0, "Government Office", "Precast Concrete", 6, 1, 2010, "N", 20000.0],
        ["LOC-008", "1600 Amphitheatre Pkwy", "Mountain View", "CA", 94043, "Santa Clara", "USA", 31000000.0, 7800000.0, 2800000.0, "R&D Campus", "Steel", 4, 3, 2019, "Y", 500000.0],
    ]

    for row in data:
        ws.append(row)

    file_path = os.path.join(SAMPLE_DIR, "Sample_SOV_1_Standard.xlsx")
    wb.save(file_path)
    print(f"Created {file_path}")

def create_sample_2_semantic():
    """
    Sample 2: Ambiguous or abbreviated headers (semantic matching test).
    Contains: "Loc #", "Property Address", "Bldg Repl Cost", "Content Value",
    "Business Interruption", "Fire Prot.", "Yr Built", "Stories".
    Includes planted anomalies:
    - Negative building value (-450000)
    - Currency symbol in Contents ($1,250,000)
    - Year Built in future (2035)
    - Inconsistent state ("California" instead of "CA")
    - Non-standard sprinkler ("Yes", "100%", "None")
    - Storey below 1 (0 storeys)
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Assets_Summary"

    headers = [
        "Loc #", "Property Address", "City", "State/Prov", "Postal Code", "County", "Nation",
        "Bldg Repl Cost", "Content Value", "Business Interruption", "Occupancy Description",
        "Const Type", "Stories", "No of Bldgs", "Yr Built", "Fire Prot.", "Misc Value"
    ]
    ws.append(headers)

    data = [
        ["L-101", "124 Market St", "San Francisco", "California", "94105", "San Francisco", "USA", -450000, "$1,250,000", "500000", "Retail Warehouse", "Masonry", 0, 1, 2035, "Yes", "15000"],
        ["L-102", "88 Pine St", "New York", "NY", "10005", "New York", "USA", 14500000, "2400000", "$850,000", "Financial Services", "Steel", 28, 1, 2014, "Y13", "0"],
        ["L-103", "456 Peachtree Rd", "Atlanta", "Georgia", "30326", "Fulton", "USA", 8900000, "$920,000", "400000", "Medical Office", "Concrete", 5, 2, 2011, "100%", "50000"],
        ["L-104", "1000 Brickell Ave", "Miami", "FL", "33131", "Miami-Dade", "USA", 18200000, "3100000", "1200000", "Residential Highrise", "Reinforced Concrete", 32, 1, 2020, "Y", "200000"],
        ["L-105", "2500 CityWest Blvd", "Houston", "Texas", "77042", "Harris", "USA", 7300000, "1100000", "450000", "Energy Exploration", "Steel Frame", 8, 1, 2005, "None", "35000"],
        ["L-106", "333 W Wacker Dr", "Chicago", "IL", "60606", "Cook", "USA", 24000000, "5200000", "1800000", "Commercial Banking", "Glass/Steel", 36, 1, 1983, "Y", "450000"],
    ]

    for row in data:
        ws.append(row)

    file_path = os.path.join(SAMPLE_DIR, "Sample_SOV_2_Complex_Semantic.xlsx")
    wb.save(file_path)
    print(f"Created {file_path}")

def create_sample_3_multisheet_messy():
    """
    Sample 3: Multi-sheet layout with missing columns, title banner at top (header at Row 4).
    Sheet 1: 'Instructions' (Reject)
    Sheet 2: 'Location Schedule' (Primary, Header Row 4, merged banner rows 1-3)
    Sheet 3: 'Summary Metrics' (Reject / Secondary)
    """
    wb = openpyxl.Workbook()

    # Sheet 1: Instructions (Reject)
    ws1 = wb.active
    ws1.title = "Instructions & Notes"
    ws1.append(["STATEMENT OF VALUES SUBMISSION GUIDELINES - CONFIDENTIAL"])
    ws1.append(["1. Complete all location details in the 'Location Schedule' tab."])
    ws1.append(["2. Replacement cost values must reflect 2026 appraisal data."])
    ws1.append(["3. Contact underwriter at underwriting@example.com for questions."])
    ws1.append(["Legend: ISO 1 = Frame, ISO 2 = Joisted Masonry, ISO 3 = Non-Combustible, ISO 4 = Masonry Non-Combustible."])

    # Sheet 2: Location Schedule (Primary, headers at Row 4)
    ws2 = wb.create_sheet(title="Location Schedule")
    ws2.append(["CLIENT STATEMENT OF VALUES - COMMERCIAL PROPERTY PORTFOLIO"])
    ws2.append(["Policyholder: Redwood Housing LLC | Effective Date: 2026-01-01"])
    ws2.append([]) # Row 3 blank

    # Row 4 headers
    headers_ws2 = [
        "Site ID", "Premise Address", "Town", "State Code", "Zipcode", "Jurisdiction County",
        "Building RCN", "BPP / Personal Property", "Time Element BI", "Occupancy Use",
        "Wall Construction", "Levels", "Units / Buildings", "Construction Year", "Sprinklered"
    ]
    ws2.append(headers_ws2)

    data_ws2 = [
        ["SITE-A1", "101 Ocean Blvd", "Santa Monica", "CA", "90401", "Los Angeles", "$6,400,000", "$850,000", "$320,000", "Hospitality / Hotel", "Concrete", 4, 1, 2016, "Y"],
        ["SITE-A2", "500 Pinecrest Way", "Boulder", "CO", "80302", "Boulder", "$4,800,000", "$620,000", "$210,000", "Research Lab", "Masonry", 3, 1, 2013, "NFPA 13"],
        ["SITE-A3", "770 Elm St", "Manchester", "NH", "03101", "Hillsborough", "$3,200,000", "$410,000", "$150,000", "Distribution Center", "Pre-engineered Steel", 1, 1, 2009, "Y"],
        ["SITE-A4", "1200 Grand Ave", "Des Moines", "IA", "50309", "Polk", "$5,100,000", "$730,000", "$280,000", "Regional Bank", "Steel", 5, 1, 2017, "Full"],
        ["SITE-A5", "900 Biscayne Blvd", "Miami", "FL", "33132", "Miami-Dade", "$28,500,000", "$3,900,000", "$1,600,000", "Luxury Condominium", "Post-tensioned Concrete", 45, 1, 2021, "Y(13R)"],
        ["SITE-A6", "350 S Main St", "Salt Lake City", "UT", "84101", "Salt Lake", "$7,800,000", "$940,000", "$380,000", "Corporate Office", "Steel", 9, 1, 2015, "Y"],
    ]

    for row in data_ws2:
        ws2.append(row)

    # Sheet 3: Summary Rollup (Secondary/Reject)
    ws3 = wb.create_sheet(title="Summary Rollup")
    ws3.append(["State", "Total TIV", "Count"])
    ws3.append(["CA", "$7,570,000", 1])
    ws3.append(["CO", "$5,630,000", 1])
    ws3.append(["FL", "$34,000,000", 1])

    file_path = os.path.join(SAMPLE_DIR, "Sample_SOV_3_MultiSheet_Messy.xlsx")
    wb.save(file_path)
    print(f"Created {file_path}")

if __name__ == "__main__":
    create_sample_1_standard()
    create_sample_2_semantic()
    create_sample_3_multisheet_messy()
