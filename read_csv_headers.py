#!/usr/bin/env python3
"""
Script pour lire les en-têtes des fichiers CSV d'accidents corporels
"""

import csv
import os

def read_csv_header(file_path):
    """Lire seulement la première ligne (en-tête) d'un fichier CSV"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file, delimiter=';')
            header = next(csv_reader)
            return header
    except Exception as e:
        print(f"Erreur lecture {file_path}: {e}")
        return None

def analyze_year_files(year):
    """Analyser les fichiers CSV d'une année donnée"""
    base_path = f"../SGBD/Metadata/mobilite/{year}"
    
    if year >= 2019:  # Format récent
        files_to_check = [
            f'caract-{year}.csv',
            f'lieux-{year}.csv', 
            f'vehicules-{year}.csv',
            f'usagers-{year}.csv'
        ]
    else:  # Format ancien
        files_to_check = [
            f'caracteristiques_{year}.csv',
            f'lieux_{year}.csv', 
            f'vehicules_{year}.csv',
            f'usagers_{year}.csv'
        ]
    
    print(f"\n{'='*50}")
    print(f"ANNÉE {year}")
    print(f"{'='*50}")
    
    for filename in files_to_check:
        file_path = os.path.join(base_path, filename)
        print(f"\n=== {filename} ===")
        
        header = read_csv_header(file_path)
        if header:
            print(f"Nombre de colonnes: {len(header)}")
            print("Variables:")
            for i, col in enumerate(header, 1):
                print(f"{i:2d}. {col}")
        else:
            print("Erreur lors de la lecture")

def compare_years():
    """Comparer la structure entre différentes années"""
    years = [2005, 2010, 2015, 2020, 2023]
    
    for year in years:
        analyze_year_files(year)

if __name__ == "__main__":
    compare_years() 