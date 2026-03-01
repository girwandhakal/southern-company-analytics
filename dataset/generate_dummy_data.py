import pandas as pd
import numpy as np
import random
import string
import os

def generate_random_site_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_random_city():
    cities = ['Springfield', 'Riverside', 'Centerville', 'Franklin', 'Greenville', 'Fairview', 'Salem', 'Madison', 'Georgetown', 'Arlington', 'Ashland', 'Clinton', 'Oxford', 'Jackson', 'Chester']
    return random.choice(cities)

def generate_random_address():
    streets = ['Main St', 'Oak St', 'Pine St', 'Maple Ave', 'Washington St', 'Park Ave', '2nd St', 'Elm St', 'View Dr', 'Lake Rd']
    return f"{random.randint(100, 9999)} {random.choice(streets)}"

def generate_random_zip():
    return f"{random.randint(10000, 99999)}"

def generate_dummy_data():
    num_sites = 7000
    extra_states = ['AK', 'HI', 'ID', 'MT', 'WY', 'ND', 'SD', 'NE', 'KS', 'NM', 'NV', 'UT', 'VT', 'NH', 'ME', 'RI', 'DE']
    all_states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'] + extra_states
    
    # 1. Generate SOLID sheet data
    solid_data = []
    site_codes = [generate_random_site_code() for _ in range(num_sites)]
    cities = [generate_random_city() for _ in range(num_sites)]
    states = [random.choice(all_states) for _ in range(num_sites)]
    
    for i in range(num_sites):
        solid_data.append({
            'Site Code': site_codes[i],
            'Site Name': f"Site {site_codes[i]} {cities[i]}",
            'Street Address 1': generate_random_address(),
            'Street Address 2': '',
            'City': cities[i],
            'State': states[i],
            'Zip': generate_random_zip()
        })
    df_solid = pd.DataFrame(solid_data)
    
    # 2. Generate SOLID-Loc sheet data (has one extra row in original, similar columns)
    solid_loc_data = []
    # Add one more site just to mimic the shapes
    site_codes_loc = site_codes + [generate_random_site_code()]
    cities_loc = cities + [generate_random_city()]
    states_loc = states + [random.choice(all_states)]
    
    for i in range(len(site_codes_loc)):
        solid_loc_data.append({
            'Site Code': site_codes_loc[i],
            'Site Name': f"Site {site_codes_loc[i]} {cities_loc[i]}",
            'Street Address 1': generate_random_address(),
            'Street Address 2': '',
            'City': cities_loc[i],
            'State': states_loc[i],
            'Zip': generate_random_zip()
        })
    df_solid_loc = pd.DataFrame(solid_loc_data)
    
    # 3. Generate ModelData sheet (167 rows, 24 cols)
    # Model, Model Parent, Labor-SE, Labor-DE, Labor-FO ...
    model_data = []
    for i in range(167):
        model_name = f"MODEL-{random.randint(1000, 9999)}"
        # Mock 24 columns based on observed types
        row = {
            'Model': model_name,
            'Model Parent': f"{model_name}-PARENT",
            'Col3': f"Val-{i}",
            'Col4': f"Val-{i}",
            'Col5': f"Val-{i}",
            'Col6': f"Val-{i}",
            'Col7': f"Val-{i}",
            'Col8': f"Val-{i}",
            'Col9': f"Val-{i}",
            'Col10': f"Val-{i}",
            'Col11': f"Val-{i}",
            'Col12': f"Val-{i}",
            'Col13': f"Val-{i}",
            'Col14': f"Val-{i}",
            'Col15': f"Val-{i}",
            'Col16': f"Val-{i}",
            'Col17': f"Val-{i}",
            'Col18': f"Val-{i}",
            'Col19': f"Val-{i}",
            'Col20': f"Val-{i}",
            'Labor-SE': round(random.uniform(100, 5000), 2),
            'Labor-DE': round(random.uniform(100, 5000), 2),
            'Labor-FO': round(random.uniform(100, 5000), 2),
            'Col24': round(random.uniform(10, 100), 2)
        }
        model_data.append(row)
    df_model_data = pd.DataFrame(model_data)
    
    # 4. Generate Pricing sheet (133 rows, 9 cols)
    # Parent Product, Product, ..., Labor-DE, Labor-SE, Labor-FO
    pricing_data = []
    for i in range(133):
        product_name = f"PROD-{random.randint(100, 999)}"
        row = {
            'Parent Product': f"PARENT-{product_name}",
            'Product': product_name,
            'Col3': f"Desc-{i}",
            'Col4': round(random.uniform(500, 10000), 2),
            'Col5': round(random.uniform(500, 10000), 2),
            'Col6': round(random.uniform(500, 10000), 2),
            'Labor-DE': round(random.uniform(100, 5000), 2),
            'Labor-SE': round(random.uniform(100, 5000), 2),
            'Labor-FO': round(random.uniform(100, 5000), 2)
        }
        pricing_data.append(row)
    df_pricing = pd.DataFrame(pricing_data)
    
    # Use actual column names from original dataset
    # We will just write these out. For ModelData/Pricing, we will fetch exact columns below if possible, 
    # but since we already got them as list from the previous terminal output, we will just use those exact names.
    
    # Actually, let's read the exact columns from the original file to ensure PERFECT match
    original_path = os.path.join(os.path.dirname(__file__), 'UAInnovateDataset-SoCo.xlsx')
    output_path = os.path.join(os.path.dirname(__file__), 'UAInnovateDataset-SoCo-Dummy.xlsx')

    try:
        xls_orig = pd.ExcelFile(original_path)
        
        # solid
        df_solid_orig = xls_orig.parse('SOLID')
        df_solid = pd.DataFrame(solid_data)
        # Ensure exact same columns (even if empty)
        for col in df_solid_orig.columns:
            if col not in df_solid.columns:
                df_solid[col] = ''
        df_solid = df_solid[df_solid_orig.columns]

        # solid-loc
        df_solid_loc_orig = xls_orig.parse('SOLID-Loc')
        df_solid_loc = pd.DataFrame(solid_loc_data)
        for col in df_solid_loc_orig.columns:
            if col not in df_solid_loc.columns:
                df_solid_loc[col] = ''
        df_solid_loc = df_solid_loc[df_solid_loc_orig.columns]

        # modeldata
        df_model_orig = xls_orig.parse('ModelData')
        # We need to fill random values for numeric and string for object
        model_data_exact = []
        for i in range(167):
            row = {}
            for col, dtype in zip(df_model_orig.columns, df_model_orig.dtypes):
                if pd.api.types.is_numeric_dtype(dtype):
                    row[col] = round(random.uniform(10, 5000), 2)
                else:
                    if col == 'Model':
                        row[col] = f"MODEL-{random.randint(1000, 9999)}"
                    else:
                        row[col] = f"RandomStr-{i}"
            model_data_exact.append(row)
        df_model_data = pd.DataFrame(model_data_exact)

        # pricing
        df_pricing_orig = xls_orig.parse('Pricing')
        pricing_data_exact = []
        for i in range(133):
            row = {}
            for col, dtype in zip(df_pricing_orig.columns, df_pricing_orig.dtypes):
                if pd.api.types.is_numeric_dtype(dtype):
                    row[col] = round(random.uniform(10, 5000), 2)
                else:
                    if col == 'Product':
                        row[col] = f"PROD-{random.randint(100, 999)}"
                    else:
                        row[col] = f"RandomStr-{i}"
            pricing_data_exact.append(row)
        df_pricing = pd.DataFrame(pricing_data_exact)

    except Exception as e:
        print(f"Failed to read exact columns from orig: {e}")
        # fallback to the mapped ones is already there but with wrong col names
        pass

    # Save to Excel with all sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_solid.to_excel(writer, sheet_name='SOLID', index=False)
        df_solid_loc.to_excel(writer, sheet_name='SOLID-Loc', index=False)
        if 'df_model_data' in locals():
            df_model_data.to_excel(writer, sheet_name='ModelData', index=False)
        if 'df_pricing' in locals():
            df_pricing.to_excel(writer, sheet_name='Pricing', index=False)
            
    print(f"Generated dummy dataset with all sheets at {output_path}")

if __name__ == '__main__':
    generate_dummy_data()
