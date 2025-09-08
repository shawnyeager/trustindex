#!/usr/bin/env python3
"""
CPI ETL Job - Transparency International Corruption Perceptions Index
Downloads, processes, and loads CPI data into the trust index database
"""

import os
import sys
import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import click
from pathlib import Path
from typing import Dict, List, Tuple
import hashlib
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class CPIProcessor:
    def __init__(self):
        self.project_root = project_root
        self.raw_data_dir = self.project_root / 'data' / 'raw'
        self.staging_dir = self.project_root / 'data' / 'staging'
        self.reference_dir = self.project_root / 'data' / 'reference'
        
        # Ensure directories exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Load ISO mappings
        self.iso_mappings = self._load_iso_mappings()
        
    def _load_iso_mappings(self) -> Dict[str, str]:
        """Load country name to ISO3 mappings"""
        iso_map_path = self.reference_dir / 'iso_map.csv'
        if not iso_map_path.exists():
            print(f"Warning: ISO mapping file not found at {iso_map_path}")
            return {}
            
        df = pd.read_csv(iso_map_path)
        return dict(zip(df['name'], df['iso3']))
    
    def download_cpi_data(self, year: int) -> Path:
        """Download CPI data for specified year"""
        # TI publishes CPI data with different URL patterns
        # For this MVP, we'll simulate the download with mock data
        
        year_dir = self.raw_data_dir / 'cpi' / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = year_dir / 'cpi.csv'
        
        if output_path.exists():
            print(f"CPI data for {year} already exists at {output_path}")
            return output_path
        
        # For MVP: Create mock CPI data based on real 2023 scores
        mock_cpi_data = [
            {'Country', 'ISO3', f'CPI {year}', 'Rank'},
            ['Sweden', 'SWE', 76, 5],
            ['United States', 'USA', 69, 15], 
            ['Brazil', 'BRA', 38, 104],
            ['Nigeria', 'NGA', 25, 150],
            ['India', 'IND', 40, 93],
            ['Germany', 'DEU', 79, 9],
            ['Japan', 'JPN', 73, 18],
            ['South Africa', 'ZAF', 43, 83],
            ['United Kingdom', 'GBR', 71, 20],
            ['France', 'FRA', 72, 21]
        ]
        
        # Convert to DataFrame and save
        df = pd.DataFrame(mock_cpi_data[1:], columns=mock_cpi_data[0])
        df.to_csv(output_path, index=False)
        
        print(f"Downloaded mock CPI data for {year} to {output_path}")
        return output_path
        
    def process_cpi_data(self, input_path: Path, year: int) -> List[Tuple]:
        """Process raw CPI CSV into normalized observations"""
        df = pd.read_csv(input_path)
        
        observations = []
        
        for _, row in df.iterrows():
            country_name = row['Country']
            iso3 = row.get('ISO3') or self._map_country_to_iso3(country_name)
            
            if not iso3:
                print(f"Warning: Could not map '{country_name}' to ISO3 code")
                continue
                
            cpi_score = row[f'CPI {year}']
            
            if pd.isna(cpi_score):
                continue
                
            # CPI scores are already 0-100, higher = less corrupt (better governance)
            observation = (
                iso3,
                year,
                'CPI',  # source
                'governance',  # trust_type
                float(cpi_score),  # raw_value
                'CPI Score (0-100)',  # raw_unit
                float(cpi_score),  # score_0_100 (already normalized)
                None,  # sample_n
                f'Transparency International CPI {year}',  # method_notes
                f'https://www.transparency.org/en/cpi/{year}'  # source_url
            )
            
            observations.append(observation)
            
        print(f"Processed {len(observations)} CPI observations for {year}")
        return observations
    
    def _map_country_to_iso3(self, country_name: str) -> str:
        """Map country name to ISO3 code"""
        # Direct lookup
        if country_name in self.iso_mappings:
            return self.iso_mappings[country_name]
            
        # Fuzzy matching for common variations
        name_variations = {
            'United States of America': 'USA',
            'United Kingdom of Great Britain and Northern Ireland': 'GBR',
            'Russian Federation': 'RUS'
        }
        
        return name_variations.get(country_name, '')
        
    def load_to_database(self, observations: List[Tuple]) -> None:
        """Load observations into database"""
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'trust'),
            user=os.getenv('POSTGRES_USER', 'trust'),
            password=os.getenv('POSTGRES_PASSWORD', 'trust')
        )
        
        try:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """INSERT INTO observations 
                       (iso3, year, source, trust_type, raw_value, raw_unit, 
                        score_0_100, sample_n, method_notes, source_url) 
                       VALUES %s
                       ON CONFLICT (iso3, year, source, trust_type) 
                       DO UPDATE SET
                         raw_value = EXCLUDED.raw_value,
                         score_0_100 = EXCLUDED.score_0_100,
                         method_notes = EXCLUDED.method_notes,
                         source_url = EXCLUDED.source_url,
                         ingested_at = NOW()""",
                    observations
                )
                
                conn.commit()
                print(f"Loaded {len(observations)} observations to database")
                
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    def save_staging_data(self, observations: List[Tuple], year: int) -> Path:
        """Save processed data to staging CSV"""
        staging_path = self.staging_dir / f'cpi_{year}.csv'
        
        df = pd.DataFrame(observations, columns=[
            'iso3', 'year', 'source', 'trust_type', 'raw_value', 
            'raw_unit', 'score_0_100', 'sample_n', 'method_notes', 'source_url'
        ])
        
        df.to_csv(staging_path, index=False)
        print(f"Saved staging data to {staging_path}")
        
        return staging_path

@click.command()
@click.option('--year', default=2024, help='Year to process CPI data for')
@click.option('--skip-download', is_flag=True, help='Skip download and use existing raw data')
def main(year: int, skip_download: bool):
    """Main CPI ETL process"""
    
    # Load environment
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    processor = CPIProcessor()
    
    print(f"Starting CPI ETL for year {year}")
    
    try:
        # Download data
        if not skip_download:
            raw_data_path = processor.download_cpi_data(year)
        else:
            raw_data_path = processor.raw_data_dir / 'cpi' / str(year) / 'cpi.csv'
            if not raw_data_path.exists():
                raise FileNotFoundError(f"Raw data not found at {raw_data_path}")
        
        # Process data
        observations = processor.process_cpi_data(raw_data_path, year)
        
        # Save staging data
        processor.save_staging_data(observations, year)
        
        # Load to database
        processor.load_to_database(observations)
        
        print(f"✅ CPI ETL completed successfully for year {year}")
        
    except Exception as e:
        print(f"❌ CPI ETL failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()