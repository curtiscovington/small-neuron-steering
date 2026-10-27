# One-neuron smallness steering in Qwen3-8B

A standalone reproduction package for Curtis Covington's article, **Can One Neuron Make Qwen Describe Smaller Things?** Inspired by [Sauers' post](https://x.com/Sauers_/status/2114565634789142785).

Increasing layer 17, neuron 11605 by about 8.33 increased clearly-small main subjects from 9/64 to 43/64 under the author's ratings. This is a context-dependent result on authored creature/object prompts. Original Codex and Qwen ratings and an exploratory guided-Qwen re-rating are included separately.

## Recompute the saved results (no GPU)

Python 3.10+; only the standard library is needed:

```sh
python analyze.py --reviewer human
python analyze.py --reviewer codex
python analyze.py --reviewer qwen
python analyze.py --reviewer guided
python -m unittest discover -s tests -v
```

The human analysis test compares all condition counts, paired comparisons, corrected p-values, and quality results against the saved published analysis. Guided ratings are exploratory because their instructions were revised after inspecting disagreements.

## Generate a new set of replies

The original used a DGX Spark with NVIDIA GB10, BF16 Qwen3-8B, SDPA attention, greedy decoding, and thinking disabled. Use a compatible CUDA environment with enough memory for the model (roughly 16 GB for weights plus runtime overhead). These scripts download the pinned model revision from Hugging Face if needed. Model access and terms remain the user's responsibility.

`requirements.txt` records the installed generation-library versions; GPU/ARM wheel installation depends on the machine. It is not a universal wheel-installation recipe. In a compatible environment:

```sh
pip install -r requirements.txt
python run_followup.py --out runs/my-followup
```

The 448 tasks are read directly from the frozen protocol. The runner adds the saved offsets to MLP activations immediately before `down_proj`, on prompt and generated tokens. Model weights are unchanged. Every reply is checkpointed in `runs/my-followup/state.json`. New output never replaces bundled research results. Runtime/package details are saved in `environment.json`.

To pause, press Ctrl-C once, or create a marker from another terminal:

```sh
touch runs/my-followup/pause
```

The current reply finishes and is saved. To resume:

```sh
rm -f runs/my-followup/pause
python run_followup.py --out runs/my-followup
```

Completed task keys are skipped. A file lock prevents two workers using the same directory; changes to the frozen settings are rejected. Changing hardware or libraries may change exact text. The extracted runner has unit tests, but this release has not generated a fresh 448-reply GPU reproduction.

## Optional Qwen reviewer

Use a separately running Ollama endpoint with the exact model tag and digest in the review protocol. The historical tag is `qwen3.8:27b-q4_K_M`; availability elsewhere is not assumed. The worker verifies its digest and fails if it is absent. It does not install or start Ollama, manage other models, or stop local services.

```sh
python review_qwen.py --endpoint http://127.0.0.1:11434 --out runs/original-review
python review_qwen.py --guided --endpoint http://127.0.0.1:11434 --out runs/guided-review
```

To rate newly generated replies, add `--responses runs/my-followup/state.json`. Only conversation and reply text are sent to the reviewer. Conditions, neuron IDs, and other ratings are excluded. Raw requests and responses are retained. A pause marker works as above; rerunning resumes saved ratings. Server failures stop the worker immediately instead of exhausting the queue. Malformed/truncated output also stops for inspection; preserve the failed artifact before retrying. Invalid evidence quotations are flagged without rewriting the rating.

Analyze new reviews with:

```sh
python analyze.py --responses runs/my-followup/state.json --ratings runs/original-review/state.json
```

Only analyze a full matched set of 448 replies and ratings. Do not reuse the bundled ratings to score new generated text.

## Contents and provenance

- `steer.py`: model loading, intervention hook, generation.
- `run_followup.py`: resumable generation worker.
- `analysis_core.py`: original paired-test and Holm-analysis functions extracted from the Lab.
- `analyze.py`: saved-data analysis CLI.
- `review_qwen.py`: optional, condition-hidden reviewer.
- `protocols/`: fixed follow-up tasks and original/guided review instructions.
- `results/`: original responses, ratings, summaries, and initial screening evidence.
- `tests/`: numerical regression, pause/resume, rating isolation, and tensor-hook cleanup tests.
- `SHA256SUMS`: hashes of release files.

Human free-text notes are omitted from this package; numerical ratings are unchanged. Reviewer protocols are explicitly labeled public exports where host metadata or unrelated queue jobs were removed. Their source hashes refer to the original research artifacts, not modified exports. `SHA256SUMS` hashes the files actually distributed. The frozen follow-up protocol itself is unchanged in content.

Code was extracted from the original local `datacenter-lab/experiments/neuron_discovery` runtime: `automatic_service.py`, `anchor_service.py`, `small_followup_protocol.py`, `concept_benchmark_protocol.py`, `qwen_reply_review.py`, and `guided_review_queue.py`. Standalone wiring is new. This is the focused follow-up package, not the full atlas-discovery system or the Lab UI.

## Limits

One checkpoint, a fixed prompt bank, two random-neuron controls, and reviewers who were not wholly unexposed to prior findings. The three original rating sets describe the same outputs, not independent replications. Guided re-rating must not replace them. The quality checks do not rule out every side effect.
