from __future__ import annotations

import traceback

from src.extract import extract_data
from src.load import load_to_postgres
from src.quality import run_quality_checks
from src.transform import save_transformed_data, transform_data


def run_pipeline() -> None:
    """
    Execute the complete marketing data pipeline in the required order.
    """
    print("[pipeline] Iniciando pipeline")

    print("[pipeline] Extraindo dados")
    extracted_data = extract_data()

    print("[pipeline] Transformando dados")
    tables = transform_data(extracted_data)

    print("[pipeline] Executando validacoes")
    run_quality_checks(tables)

    print("[pipeline] Salvando arquivos processados")
    output_paths = save_transformed_data(tables)
    for table_name, path in output_paths.items():
        print(f"[pipeline] - {table_name}: {path}")

    print("[pipeline] Carregando dados no PostgreSQL")
    load_to_postgres(tables)

    print("[pipeline] Pipeline concluido com sucesso")


def main() -> None:
    try:
        run_pipeline()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[pipeline] ERRO: {exc}")
        raise SystemExit(1) from exc
    except Exception as exc:  # pragma: no cover
        print("[pipeline] ERRO inesperado durante execucao do pipeline.")
        print(f"[pipeline] Detalhes: {exc}")
        traceback.print_exc()
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
