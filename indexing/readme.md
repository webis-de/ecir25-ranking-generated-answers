# Retrieval Pipelines

The code for the different retrieval models is split in different files.
- Baseline retrieval is run using the run_base_retrievals.sh script, which runs the base_retrieval_evaluation.py script for each of the baseline pipelines, once with and once without query expansion
- the colbert v1 and monot5 pipelines are run using the querywise_indexing_execution_script.sh, which runs the respective querywise_indexing_*.py scripts for them
- the duot5 pipeline was run in google colab, the slightly adapted code is in its own subfolder colab_duot5
- colbert v2 is run directly using the official github repository and the results are imported manually

The results for all pipelines are in the results directory, including some visualizations.