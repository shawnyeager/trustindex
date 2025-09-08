#!/usr/bin/env python3
"""
Development seed script for Global Trust Index
Loads reference countries and creates mock observations
"""

import os
import sys
import csv
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_db_connection():
    """Get database connection using environment variables"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'trust'),
        user=os.getenv('POSTGRES_USER', 'trust'),
        password=os.getenv('POSTGRES_PASSWORD', 'trust')
    )

def load_countries(conn):
    """Load countries from reference CSV"""
    iso_map_path = project_root / 'data' / 'reference' / 'iso_map.csv'
    
    with open(iso_map_path, 'r') as f:
        reader = csv.DictReader(f)
        countries = list(reader)
    
    # Insert countries
    with conn.cursor() as cur:
        execute_values(
            cur,
            """INSERT INTO countries (iso3, iso2, name, region, income_group) 
               VALUES %s ON CONFLICT (iso3) DO NOTHING""",
            [(c['iso3'], c['iso2'], c['name'], c['region'], c['income_group']) 
             for c in countries]
        )
    
    print(f"Loaded {len(countries)} countries")
    return countries

def create_mock_observations(conn, countries):
    """Create mock CPI-based observations for demo"""
    observations = []
    
    # Mock CPI scores for 2023 and 2024
    cpi_scores = {
        'SWE': 76, 'USA': 69, 'BRA': 38, 'NGA': 25, 'IND': 40,
        'DEU': 79, 'JPN': 73, 'ZAF': 43, 'GBR': 71, 'FRA': 72
    }
    
    for country in countries[:5]:  # First 5 countries for MVP
        iso3 = country['iso3']
        base_score = cpi_scores.get(iso3, 50)
        
        for year in [2023, 2024]:
            # Add some year-to-year variation
            score_variation = random.uniform(-3, 3)
            final_score = max(0, min(100, base_score + score_variation))
            
            observations.append((
                iso3, year, 'CPI', 'governance',
                final_score, 'CPI Score', final_score,
                None, 'Mock CPI data for development',
                'https://www.transparency.org/en/cpi'
            ))
    
    # Insert observations
    with conn.cursor() as cur:
        execute_values(
            cur,
            """INSERT INTO observations 
               (iso3, year, source, trust_type, raw_value, raw_unit, 
                score_0_100, sample_n, method_notes, source_url) 
               VALUES %s ON CONFLICT (iso3, year, source, trust_type) DO NOTHING""",
            observations
        )
    
    print(f"Created {len(observations)} mock observations")

def compute_country_year(conn):
    """Compute country_year entries from observations"""
    with conn.cursor() as cur:
        # Simple computation: for MVP, GTI = governance score (CPI only)
        cur.execute("""
            INSERT INTO country_year (iso3, year, governance, gti, confidence_score, confidence_tier, sources_used)
            SELECT 
                o.iso3,
                o.year,
                o.score_0_100 as governance,
                o.score_0_100 as gti,  -- For MVP, GTI = governance proxy
                1.0 as confidence_score,
                'C' as confidence_tier,  -- Proxy only
                jsonb_build_object('governance', jsonb_build_array('CPI')) as sources_used
            FROM observations o
            WHERE o.trust_type = 'governance' AND o.source = 'CPI'
            ON CONFLICT (iso3, year) DO UPDATE SET
                governance = EXCLUDED.governance,
                gti = EXCLUDED.gti,
                confidence_score = EXCLUDED.confidence_score,
                confidence_tier = EXCLUDED.confidence_tier,
                sources_used = EXCLUDED.sources_used,
                computed_at = NOW()
        """)
        
        rows_affected = cur.rowcount
        print(f"Computed {rows_affected} country-year entries")

def main():
    """Main seeding function"""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        env_path = project_root / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        conn = get_db_connection()
        
        print("Starting database seeding...")
        
        # Load countries
        countries = load_countries(conn)
        
        # Create mock observations
        create_mock_observations(conn, countries)
        
        # Compute country_year aggregations
        compute_country_year(conn)
        
        conn.commit()
        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()