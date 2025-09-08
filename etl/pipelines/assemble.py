#!/usr/bin/env python3
"""
Assembly Pipeline - Compute GTI scores from raw observations
Aggregates pillar scores and computes final GTI with confidence metrics
"""

import os
import sys
import psycopg2
import click
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class CountryYearScore:
    iso3: str
    year: int
    interpersonal: Optional[float] = None
    institutional: Optional[float] = None
    governance: Optional[float] = None
    gti: Optional[float] = None
    confidence_score: float = 0.0
    confidence_tier: str = 'C'
    sources_used: Dict[str, List[str]] = None

class GTIAssembler:
    def __init__(self):
        self.project_root = project_root
        
        # GTI weights from methodology
        self.weights = {
            'interpersonal': 0.3,
            'institutional': 0.4, 
            'governance': 0.3
        }
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'trust'),
            user=os.getenv('POSTGRES_USER', 'trust'),
            password=os.getenv('POSTGRES_PASSWORD', 'trust')
        )
    
    def fetch_pillar_scores(self, conn, year: int, sources: Optional[List[str]] = None) -> List[CountryYearScore]:
        """Fetch and aggregate pillar scores for all countries in a given year"""
        
        # Build source filter
        source_filter = ""
        params = [year]
        if sources:
            placeholders = ','.join(['%s'] * len(sources))
            source_filter = f"AND source IN ({placeholders})"
            params.extend(sources)
        
        with conn.cursor() as cur:
            # Get all observations for the year
            cur.execute(f"""
                SELECT 
                    iso3, 
                    source, 
                    trust_type, 
                    score_0_100,
                    method_notes
                FROM observations 
                WHERE year = %s {source_filter}
                ORDER BY iso3, trust_type, source
            """, params)
            
            observations = cur.fetchall()
        
        # Group by country
        country_data = {}
        for iso3, source, trust_type, score, method_notes in observations:
            if iso3 not in country_data:
                country_data[iso3] = CountryYearScore(
                    iso3=iso3, 
                    year=year,
                    sources_used={}
                )
            
            country = country_data[iso3]
            
            # Map trust types to pillars
            if trust_type in ['interpersonal']:
                country.interpersonal = self._aggregate_pillar_scores(
                    country.interpersonal, score, source, trust_type
                )
                self._add_source_used(country, 'interpersonal', source)
                
            elif trust_type in ['institutional']:
                country.institutional = self._aggregate_pillar_scores(
                    country.institutional, score, source, trust_type
                )
                self._add_source_used(country, 'institutional', source)
                
            elif trust_type in ['governance', 'cpi', 'wgi']:
                country.governance = self._aggregate_pillar_scores(
                    country.governance, score, source, trust_type
                )
                self._add_source_used(country, 'governance', source)
        
        return list(country_data.values())
    
    def _aggregate_pillar_scores(self, current_score: Optional[float], new_score: float, 
                               source: str, trust_type: str) -> float:
        """Aggregate multiple scores for a pillar (simple average for MVP)"""
        if current_score is None:
            return new_score
        
        # For MVP: simple average
        # In production, this would use weighted averages based on methodology
        return (current_score + new_score) / 2
    
    def _add_source_used(self, country: CountryYearScore, pillar: str, source: str):
        """Track sources used for each pillar"""
        if country.sources_used is None:
            country.sources_used = {}
            
        if pillar not in country.sources_used:
            country.sources_used[pillar] = []
            
        if source not in country.sources_used[pillar]:
            country.sources_used[pillar].append(source)
    
    def compute_gti_scores(self, countries: List[CountryYearScore]) -> List[CountryYearScore]:
        """Compute GTI scores and confidence metrics"""
        
        for country in countries:
            # Count available pillars
            pillars_available = []
            if country.interpersonal is not None:
                pillars_available.append('interpersonal')
            if country.institutional is not None:
                pillars_available.append('institutional')  
            if country.governance is not None:
                pillars_available.append('governance')
            
            # Compute GTI based on available pillars
            if len(pillars_available) == 3:
                # All three pillars available
                country.gti = (
                    self.weights['interpersonal'] * country.interpersonal +
                    self.weights['institutional'] * country.institutional +
                    self.weights['governance'] * country.governance
                )
                country.confidence_tier = 'A'
                country.confidence_score = 1.0
                
            elif len(pillars_available) == 2:
                # Two pillars - reweight proportionally
                if 'governance' in pillars_available and 'institutional' in pillars_available:
                    country.gti = 0.6 * country.institutional + 0.4 * country.governance
                elif 'governance' in pillars_available and 'interpersonal' in pillars_available:
                    country.gti = 0.5 * country.interpersonal + 0.5 * country.governance
                elif 'institutional' in pillars_available and 'interpersonal' in pillars_available:
                    country.gti = 0.57 * country.institutional + 0.43 * country.interpersonal
                
                country.confidence_tier = 'B'
                country.confidence_score = 0.7
                
            elif 'governance' in pillars_available:
                # Governance proxy only
                country.gti = country.governance
                country.confidence_tier = 'C'
                country.confidence_score = 0.5
                
            else:
                # No valid data
                country.gti = None
                country.confidence_tier = 'C'
                country.confidence_score = 0.0
        
        return [c for c in countries if c.gti is not None]
    
    def save_country_year_scores(self, conn, countries: List[CountryYearScore]) -> None:
        """Save computed scores to country_year table"""
        
        with conn.cursor() as cur:
            for country in countries:
                sources_json = json.dumps(country.sources_used) if country.sources_used else None
                
                cur.execute("""
                    INSERT INTO country_year 
                    (iso3, year, interpersonal, institutional, governance, gti, 
                     confidence_score, confidence_tier, sources_used, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (iso3, year) 
                    DO UPDATE SET
                        interpersonal = EXCLUDED.interpersonal,
                        institutional = EXCLUDED.institutional,
                        governance = EXCLUDED.governance,
                        gti = EXCLUDED.gti,
                        confidence_score = EXCLUDED.confidence_score,
                        confidence_tier = EXCLUDED.confidence_tier,
                        sources_used = EXCLUDED.sources_used,
                        version = EXCLUDED.version,
                        computed_at = NOW()
                """, (
                    country.iso3, country.year,
                    country.interpersonal, country.institutional, country.governance, 
                    country.gti, country.confidence_score, country.confidence_tier,
                    sources_json, '0.1.0'
                ))
            
            conn.commit()
            print(f"Saved {len(countries)} country-year scores")

@click.command()
@click.option('--year', default=2024, help='Year to compute scores for')  
@click.option('--sources', help='Comma-separated list of sources to include')
def main(year: int, sources: Optional[str]):
    """Main assembly pipeline"""
    
    # Load environment
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    assembler = GTIAssembler()
    
    # Parse sources
    source_list = sources.split(',') if sources else None
    
    print(f"Starting GTI assembly for year {year}")
    if source_list:
        print(f"Including sources: {source_list}")
    
    try:
        conn = assembler.get_db_connection()
        
        # Fetch pillar scores
        countries = assembler.fetch_pillar_scores(conn, year, source_list)
        print(f"Found data for {len(countries)} countries")
        
        # Compute GTI scores
        countries_with_gti = assembler.compute_gti_scores(countries)
        print(f"Computed GTI for {len(countries_with_gti)} countries")
        
        # Save results
        assembler.save_country_year_scores(conn, countries_with_gti)
        
        # Print summary
        for country in countries_with_gti[:5]:  # Show first 5
            print(f"  {country.iso3}: GTI={country.gti:.1f}, Tier={country.confidence_tier}")
        
        print(f"✅ GTI assembly completed successfully for year {year}")
        
    except Exception as e:
        print(f"❌ GTI assembly failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()