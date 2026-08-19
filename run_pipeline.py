from __future__ import annotations

import argparse
import gc
import os
import sys
from pathlib import Path
from typing import Any

import nbformat
import pandas as pd


NOTEBOOKS = [
    "01_entendimento_e_qualidade_dos_dados.ipynb",
    "02_construcao_e_selecao_do_target.ipynb",
    "03_base_analitica_e_engenharia_de_features.ipynb",
    "04_modelagem_politica_scoring.ipynb",
]


def executar_notebook(caminho: Path, spark_compartilhado: Any | None = None) -> Any | None:
    """Executa as células de código de um notebook na ordem, sem depender de servidor Jupyter."""
    notebook = nbformat.read(caminho, as_version=4)
    namespace: dict[str, Any] = {
        "__name__": "__main__",
        "__file__": str(caminho),
    }
    if spark_compartilhado is not None:
        namespace["spark"] = spark_compartilhado

    for indice, celula in enumerate(notebook.cells):
        if celula.cell_type != "code" or not celula.source.strip():
            continue
        referencia = f"{caminho.name}:celula_{indice}"
        try:
            exec(compile(celula.source, referencia, "exec"), namespace, namespace)
        except Exception as erro:
            raise RuntimeError(f"Falha em {referencia}") from erro

    spark = namespace.get("spark", spark_compartilhado)
    namespace.clear()
    gc.collect()
    return spark


def validar_submissao(caminho: Path) -> None:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de submissão não encontrado: {caminho}")

    submissao = pd.read_csv(caminho)
    colunas_esperadas = ["id_cliente", "probabilidade_inadimplencia"]

    if submissao.columns.tolist() != colunas_esperadas:
        raise ValueError(f"Colunas inválidas: {submissao.columns.tolist()}")
    if submissao.empty:
        raise ValueError("O arquivo de submissão está vazio.")
    if submissao["id_cliente"].isna().any() or submissao["id_cliente"].duplicated().any():
        raise ValueError("Foram encontrados identificadores nulos ou duplicados.")
    if submissao["probabilidade_inadimplencia"].isna().any():
        raise ValueError("Foram encontradas probabilidades nulas.")
    if not submissao["probabilidade_inadimplencia"].between(0, 1).all():
        raise ValueError("Foram encontradas probabilidades fora do intervalo [0, 1].")

    print(
        "Submissão validada: "
        f"{len(submissao):,} linhas, {submissao['id_cliente'].nunique():,} clientes únicos."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa o pipeline completo do case técnico.")
    parser.add_argument("--data-path", default="data", help="Diretório das bases de entrada.")
    parser.add_argument("--output-path", default="outputs", help="Diretório das saídas.")
    args = parser.parse_args()

    raiz = Path(__file__).resolve().parent
    data_path = Path(args.data_path).resolve()
    output_path = Path(args.output_path).resolve()

    arquivos_obrigatorios = [
        "base_cadastral.parquet",
        "base_submissao.parquet",
        "historico_emprestimos.parquet",
        "historico_parcelas.parquet",
    ]
    ausentes = [nome for nome in arquivos_obrigatorios if not (data_path / nome).exists()]
    if ausentes:
        raise FileNotFoundError(
            f"Bases obrigatórias não encontradas em {data_path}: {', '.join(ausentes)}"
        )

    output_path.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    os.environ.setdefault("SPARK_MASTER", "local[2]")
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ["CREDIT_RISK_DATA_PATH"] = str(data_path)
    os.environ["CREDIT_RISK_OUTPUT_PATH"] = str(output_path)

    spark = None
    for nome in NOTEBOOKS:
        caminho = raiz / nome
        if not caminho.exists():
            raise FileNotFoundError(f"Notebook não encontrado: {caminho}")
        print(f"\nExecutando {nome}...")
        spark = executar_notebook(caminho, spark)
        print(f"Concluído: {nome}")

    validar_submissao(output_path / "submissao_case.csv")
    print("\nPipeline concluído sem erros.")


if __name__ == "__main__":
    main()
