from __future__ import annotations

import platform
import sys

import matplotlib
import nbformat
import numpy
import pandas
import pyarrow
import pyspark
import sklearn
from pyspark.sql import SparkSession


def main() -> None:
    print(f"Python: {platform.python_version()}")
    print(f"PySpark: {pyspark.__version__}")
    print(f"pandas: {pandas.__version__}")
    print(f"NumPy: {numpy.__version__}")
    print(f"scikit-learn: {sklearn.__version__}")
    print(f"PyArrow: {pyarrow.__version__}")
    print(f"Matplotlib: {matplotlib.__version__}")
    print(f"nbformat: {nbformat.__version__}")

    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("credit-risk-environment-check")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .getOrCreate()
    )
    try:
        if spark.range(10).count() != 10:
            raise RuntimeError("Falha no teste básico do Spark.")
        print(f"Spark: {spark.version} — teste local concluído")
    finally:
        spark.stop()

    print("Ambiente validado com sucesso.")


if __name__ == "__main__":
    main()
