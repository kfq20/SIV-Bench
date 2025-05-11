# SIV-Bench: A Video Benchmark for Social Interaction Understanding and Reasoning

<p align="center">
    <a href="https://huggingface.co/datasets/Fancylalala/SIV-Bench">
        <img alt="Build" src="https://img.shields.io/badge/🤗 Dataset-SIV Bench-yellow">
    </a>
</p>

This repository is the official implementation of **SIV-Bench**. 

## Environment Setup

This project utilizes the [VLMEvalKit](https://github.com/open-compass/VLMEvalKit) for evaluation. To ensure proper functionality and reproducible results, please configure your environment strictly according to the official VLMEvalKit documentation.

**Key Steps & Considerations:**

1.  **Follow the Official Quickstart Guide:** The primary instructions for setting up your environment can be found in the
    [VLMEvalKit Quickstart guide](https://github.com/open-compass/VLMEvalKit/blob/main/docs/en/Quickstart.md).

2.  **Dependencies and Versions:**
    * The Quickstart guide will cover the necessary dependencies. Pay close attention to the recommended versions of core libraries such as `torch`, `transformers`, and CUDA.
    * VLMEvalKit's main GitHub page may also provide specific version recommendations for `transformers` or other libraries depending on the Vision-Language Models (VLMs) you intend to evaluate. It's advisable to check there for any model-specific requirements. Discrepancies in library versions can sometimes lead to different evaluation outcomes.

3.  **API Key Configuration:** The Quickstart guide also provides instructions on how to configure any necessary API keys for proprietary models or services that VLMEvalKit might interact with.

By following the official VLMEvalKit documentation, you will be able to set up an environment suitable for running the evaluations in this repository.

## Evaluation

To run the evaluation on SIV-Bench, use the following command structure:

```bash
python run.py --config config.json --work-dir output
```

**Arguments:**

* `--config`: Path to the JSON configuration file that specifies the model(s) and dataset(s) to be evaluated, along with their respective parameters.
* `--work-dir`: Path to the directory where the evaluation results will be saved.

**Configuration File (`config.json`)**

The `config.json` file defines the parameters for the models and datasets.

* **Model Parameters:** Model-specific parameters are generally determined by VLMEvalKit and the individual model configurations.
* **Data Parameters:** Dataset parameters also largely align with VLMEvalKit standards. For the `SIV-Bench` dataset, a notable parameter is `subtitle_version`, which dictates the subtitle processing method:
    * `origin`: Uses the original subtitles as provided.
    * `w_sub`: Uses a version of the video/data with subtitles processed/included in a specific manner.
    * `wo_sub`: Uses a version of the video/data without subtitles, or with subtitles explicitly excluded/removed.

**Example `config.json`:**

```json
{
    "model": {
        "InternVL3-8B": {}
    },
    "data": {
        "SIV-Bench": {
            "class": "SIVBench",
            "nframe": 16,
            "fps": -1,
            "subtitle_version": "origin"
        }
    }
}
```

**Output:**

The evaluation script will generate a `.pkl` file in the directory specified by `--work-dir`. The output file will be named in the format `{model_name}_{dataset_name}.pkl` (e.g., `InternVL3-8B_SIV-Bench.pkl`), containing the raw output results from the model.


## Results

After generating the model output `.pkl` files as described in the "Evaluation" section, you can calculate the final evaluation scores using the provided script:

```bash
python evaluate/evaluate_sivbench.py --output_file path/to/your/model_output.pkl
```
**Required Argument:**

* `--output_file`: This argument is mandatory. It specifies the path to the `.pkl` file containing the model's output results that you want to evaluate.

**Example:**

```bash
python evaluate/evaluate_sivbench.py --output_file output/InternVL3-8B_SIV-Bench.pkl
```

This script will process the specified output file and provide the final evaluation metrics for the SIV-Bench dataset.