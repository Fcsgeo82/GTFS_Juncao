# GTFS Junção

Um script Python profissional para mesclar dois conjuntos de dados GTFS (General Transit Feed Specification).

O objetivo deste projeto é fornecer uma forma fácil e robusta de unir dois arquivos GTFS (um base e um secundário), importando do arquivo secundário apenas as rotas (e suas respectivas viagens, horários, paradas e trajetos) que ainda não existem no GTFS base.

## 🚀 Como funciona

O script `merge_gtfs.py` utiliza a biblioteca `pandas` para manipular os dados dos arquivos CSV dentro do `.zip` do GTFS. 
Ele realiza as seguintes etapas principais:
1. **Identificação**: Analisa o arquivo `routes.txt` para descobrir rotas no GTFS Secundário que não estão presentes no GTFS Base (comparando pela coluna `route_short_name`).
2. **Prevenção de Colisões**: Para evitar que IDs do GTFS Secundário entrem em conflito com os IDs do GTFS Base (ex: rotas ou paradas com o mesmo ID `"1"`), o script adiciona um sufixo (por padrão `_new_gtfs`) a todos os IDs importados.
3. **Filtragem em Cascata**: Trazendo apenas as rotas exclusivas, o script filtra os arquivos `trips.txt`, `stop_times.txt`, `stops.txt`, `shapes.txt`, `calendar.txt` e `agency.txt` para extrair somente os dados referentes a essas novas rotas.
4. **Mesclagem**: Une os dados originais do GTFS Base com os novos dados filtrados e tratados.
5. **Empacotamento**: Gera um novo arquivo `.zip` final consolidado.

## 📦 Instalação

1. Clone o repositório ou baixe os arquivos.
2. Certifique-se de ter o Python instalado (versão 3.6 ou superior recomendada).
3. Instale as dependências usando o comando:

```bash
pip install -r requirements.txt
```

## ⚙️ Como usar

1. Coloque seus dois arquivos GTFS (no formato `.zip`) na mesma pasta do script (ou saiba o caminho absoluto deles no seu computador).
2. Abra o arquivo `merge_gtfs.py` e edite a seção **PARÂMETROS DE ENTRADA / CONFIGURAÇÃO** (próximo à linha 13):

```python
GTFS_BASE_PATH = 'seu_gtfs_base.zip'
GTFS_NOVO_PATH = 'seu_gtfs_secundario.zip'
GTFS_SAIDA_PATH = 'nome_do_arquivo_final_mesclado.zip'
```

3. Execute o script no terminal:

```bash
python merge_gtfs.py
```
*(Se estiver em um ambiente como PowerShell, você pode usar `python -m merge_gtfs`)*

Ao fim da execução, o arquivo final mesclado será criado no diretório especificado.

## 📝 Boas Práticas Adotadas

* **Orientação a Objetos**: Lógica contida e encapsulada.
* **Logging Contínuo**: Acompanhamento de toda a execução e eventuais erros via módulo `logging` interno do Python.
* **Manipulação em Memória/Temp**: O processo descompacta e compacta os arquivos de forma segura utilizando o módulo `tempfile`.
