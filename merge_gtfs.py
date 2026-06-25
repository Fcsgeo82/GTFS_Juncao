import pandas as pd
import zipfile
import os
import shutil
import tempfile
import logging
from typing import Set

# ==========================================
# PARÂMETROS DE ENTRADA / CONFIGURAÇÃO
# ==========================================
# Substitua pelos caminhos dos seus arquivos GTFS

# GTFS_BASE_PATH = 'gtfs_base.zip'
GTFS_BASE_PATH = 'GTFS_DETRO_BACKUP.zip'
# GTFS_NOVO_PATH = 'gtfs_novo.zip'
GTFS_NOVO_PATH = 'GTFS_DETRO.zip'
# GTFS_SAIDA_PATH = 'gtfs_mesclado.zip'
GTFS_SAIDA_PATH = 'gtfs_detro_mesclado.zip'

# Configuração de logging para acompanhar a execução
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class GTFSMerger:
    """
    Classe responsável por mesclar dois arquivos GTFS (zip).
    Usa o GTFS base e puxa apenas as linhas (rotas) que não existem nele a partir de um segundo GTFS.
    """
    def __init__(self, base_gtfs_path: str, new_gtfs_path: str, output_gtfs_path: str):
        self.base_gtfs_path = base_gtfs_path
        self.new_gtfs_path = new_gtfs_path
        self.output_gtfs_path = output_gtfs_path
        
        # Sufixo para garantir que não haja colisões de IDs (ex: trip_id, stop_id)
        self.suffix = '_new_gtfs'
        
    def _extract_zip(self, zip_path: str, extract_dir: str):
        """Extrai um arquivo ZIP para um diretório temporário."""
        logging.info(f"Extraindo {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
    def _create_zip(self, source_dir: str, zip_path: str):
        """Cria um arquivo ZIP a partir de um diretório."""
        logging.info(f"Criando novo GTFS mesclado em {zip_path}...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)

    def _read_csv(self, file_path: str) -> pd.DataFrame:
        """Lê um arquivo CSV do GTFS retornando um DataFrame do Pandas."""
        if os.path.exists(file_path):
            # Lê tudo como string para preservar IDs originais
            return pd.read_csv(file_path, dtype=str)
        return pd.DataFrame()

    def merge(self):
        """Executa a lógica principal de mesclagem estruturada e filtragem."""
        logging.info("Iniciando processo de junção dos GTFS.")
        
        with tempfile.TemporaryDirectory() as base_dir, \
             tempfile.TemporaryDirectory() as new_dir, \
             tempfile.TemporaryDirectory() as out_dir:
            
            self._extract_zip(self.base_gtfs_path, base_dir)
            self._extract_zip(self.new_gtfs_path, new_dir)
            
            # 1. Identificar rotas
            base_routes = self._read_csv(os.path.join(base_dir, 'routes.txt'))
            new_routes = self._read_csv(os.path.join(new_dir, 'routes.txt'))
            
            if base_routes.empty or new_routes.empty:
                logging.error("Os arquivos routes.txt não foram encontrados ou estão vazios.")
                return
            
            # 'route_short_name' é utilizado para identificar a linha (ex: número do ônibus)
            base_route_names = set(base_routes['route_short_name'].dropna().unique())
            routes_to_add = new_routes[~new_routes['route_short_name'].isin(base_route_names)].copy()
            
            if routes_to_add.empty:
                logging.info("Nenhuma rota nova encontrada no segundo GTFS.")
                shutil.copyfile(self.base_gtfs_path, self.output_gtfs_path)
                return
            
            logging.info(f"Encontradas {len(routes_to_add)} novas rotas para importar.")
            
            # 2. Modificar IDs das novas rotas (Evita colisão de chaves com o GTFS base)
            routes_to_add['route_id'] = routes_to_add['route_id'] + self.suffix
            if 'agency_id' in routes_to_add.columns:
                routes_to_add['agency_id'] = routes_to_add['agency_id'] + self.suffix
                
            new_route_ids = set(routes_to_add['route_id'])
            
            # 3. Filtrar e ajustar Trips (Viagens)
            new_trips = self._read_csv(os.path.join(new_dir, 'trips.txt'))
            new_trips['route_id'] = new_trips['route_id'] + self.suffix
            trips_to_add = new_trips[new_trips['route_id'].isin(new_route_ids)].copy()
            
            trips_to_add['trip_id'] = trips_to_add['trip_id'] + self.suffix
            if 'service_id' in trips_to_add.columns:
                trips_to_add['service_id'] = trips_to_add['service_id'] + self.suffix
            if 'shape_id' in trips_to_add.columns:
                trips_to_add['shape_id'] = trips_to_add['shape_id'].apply(lambda x: x + self.suffix if pd.notna(x) else x)
                
            new_trip_ids = set(trips_to_add['trip_id'])
            new_service_ids = set(trips_to_add['service_id']) if 'service_id' in trips_to_add.columns else set()
            new_shape_ids = set(trips_to_add['shape_id'].dropna()) if 'shape_id' in trips_to_add.columns else set()
            
            # 4. Filtrar e ajustar Stop Times
            new_stop_times = self._read_csv(os.path.join(new_dir, 'stop_times.txt'))
            new_stop_times['trip_id'] = new_stop_times['trip_id'] + self.suffix
            st_to_add = new_stop_times[new_stop_times['trip_id'].isin(new_trip_ids)].copy()
            st_to_add['stop_id'] = st_to_add['stop_id'] + self.suffix
            
            new_stop_ids = set(st_to_add['stop_id'])
            
            # 5. Filtrar e ajustar Stops
            new_stops = self._read_csv(os.path.join(new_dir, 'stops.txt'))
            new_stops['stop_id'] = new_stops['stop_id'] + self.suffix
            stops_to_add = new_stops[new_stops['stop_id'].isin(new_stop_ids)].copy()
            
            # 6. Filtrar e ajustar Shapes
            shapes_to_add = pd.DataFrame()
            new_shapes = self._read_csv(os.path.join(new_dir, 'shapes.txt'))
            if not new_shapes.empty:
                new_shapes['shape_id'] = new_shapes['shape_id'] + self.suffix
                shapes_to_add = new_shapes[new_shapes['shape_id'].isin(new_shape_ids)].copy()
                
            # 7. Filtrar e ajustar Calendar e Calendar Dates
            cal_to_add = pd.DataFrame()
            new_cal = self._read_csv(os.path.join(new_dir, 'calendar.txt'))
            if not new_cal.empty and new_service_ids:
                new_cal['service_id'] = new_cal['service_id'] + self.suffix
                cal_to_add = new_cal[new_cal['service_id'].isin(new_service_ids)].copy()
                
            cal_dates_to_add = pd.DataFrame()
            new_cal_dates = self._read_csv(os.path.join(new_dir, 'calendar_dates.txt'))
            if not new_cal_dates.empty and new_service_ids:
                new_cal_dates['service_id'] = new_cal_dates['service_id'] + self.suffix
                cal_dates_to_add = new_cal_dates[new_cal_dates['service_id'].isin(new_service_ids)].copy()
                
            # 8. Filtrar e ajustar Agency
            agency_to_add = pd.DataFrame()
            new_agency = self._read_csv(os.path.join(new_dir, 'agency.txt'))
            if not new_agency.empty and 'agency_id' in routes_to_add.columns:
                new_agency['agency_id'] = new_agency['agency_id'] + self.suffix
                new_agency_ids = set(routes_to_add['agency_id'].dropna())
                agency_to_add = new_agency[new_agency['agency_id'].isin(new_agency_ids)].copy()
            elif not new_agency.empty:
                agency_to_add = new_agency.copy()
                if 'agency_id' in agency_to_add.columns:
                    agency_to_add['agency_id'] = agency_to_add['agency_id'] + self.suffix
                    routes_to_add['agency_id'] = agency_to_add['agency_id'].iloc[0]

            # 9. Combinar arquivos
            def _merge_and_save(filename: str, df_base: pd.DataFrame, df_add: pd.DataFrame):
                if df_base.empty and df_add.empty:
                    return
                combined = pd.concat([df_base, df_add], ignore_index=True)
                combined.to_csv(os.path.join(out_dir, filename), index=False)
                
            logging.info("Combinando e salvando arquivos...")
            _merge_and_save('routes.txt', base_routes, routes_to_add)
            _merge_and_save('trips.txt', self._read_csv(os.path.join(base_dir, 'trips.txt')), trips_to_add)
            _merge_and_save('stop_times.txt', self._read_csv(os.path.join(base_dir, 'stop_times.txt')), st_to_add)
            _merge_and_save('stops.txt', self._read_csv(os.path.join(base_dir, 'stops.txt')), stops_to_add)
            _merge_and_save('shapes.txt', self._read_csv(os.path.join(base_dir, 'shapes.txt')), shapes_to_add)
            _merge_and_save('calendar.txt', self._read_csv(os.path.join(base_dir, 'calendar.txt')), cal_to_add)
            _merge_and_save('calendar_dates.txt', self._read_csv(os.path.join(base_dir, 'calendar_dates.txt')), cal_dates_to_add)
            _merge_and_save('agency.txt', self._read_csv(os.path.join(base_dir, 'agency.txt')), agency_to_add)
            
            # Copiar arquivos não manipulados do base
            standard_files = ['routes.txt', 'trips.txt', 'stop_times.txt', 'stops.txt', 'shapes.txt', 'calendar.txt', 'calendar_dates.txt', 'agency.txt']
            for file in os.listdir(base_dir):
                if file not in standard_files and file.endswith('.txt'):
                    shutil.copyfile(os.path.join(base_dir, file), os.path.join(out_dir, file))
                    
            self._create_zip(out_dir, self.output_gtfs_path)
            logging.info("Processo de mesclagem concluído com sucesso!")

if __name__ == '__main__':
    # ==========================================
    # EXECUÇÃO DO SCRIPT
    # ==========================================
    if not os.path.exists(GTFS_BASE_PATH):
        logging.error(f"Arquivo base ausente: {GTFS_BASE_PATH}")
    elif not os.path.exists(GTFS_NOVO_PATH):
        logging.error(f"Arquivo novo ausente: {GTFS_NOVO_PATH}")
    else:
        merger = GTFSMerger(base_gtfs_path=GTFS_BASE_PATH, new_gtfs_path=GTFS_NOVO_PATH, output_gtfs_path=GTFS_SAIDA_PATH)
        merger.merge()
