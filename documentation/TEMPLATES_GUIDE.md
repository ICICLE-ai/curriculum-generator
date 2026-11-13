# Curriculum Modules Guide

Smart Curriculum Designer builds your course one week (one **module**) at a time. There is no fixed catalogue of modules: every week is written for your subject, your learning outcomes and the results of your own run on your own images. This guide explains what you get for each week, how it is produced and checked, and how to describe weeks so the result matches what you want to teach.

## Table of Contents
1. [What Each Week Contains](#what-each-week-contains)
2. [How a Week Is Built](#how-a-week-is-built)
3. [The Lecture Slides](#the-lecture-slides)
4. [Writing Good Weeks](#writing-good-weeks)
5. [Built-in Presets](#built-in-presets)
6. [Using a Week in Class](#using-a-week-in-class)

---

## What Each Week Contains

Each week has its own folder, `exercises/Week_{xx}/{module}/`:

| File | For | What it is |
| --- | --- | --- |
| `{module}_overview.md` | Students | The week's handout: the real-world problem, the concepts behind it, how it connects to your dataset's results, and what students build in each of three milestones. |
| `{module}_exercise.py` | Students | Starter code with docstrings, type hints and `# TODO` steps for each milestone. |
| `{module}_test.py` | Students & instructors | Unit tests for the week. They import `{module}_exercise`, so they check the student's work; all of them passed against the reference solution first. |
| `{module}_solution.py` | Instructors | The complete reference solution. |
| `{module}_presentation.pptx` | Instructors | Widescreen lecture slides for the week (typically 17–21 slides). |
| `{module}_verification.json` | Instructors | Confirms the solution passed every test, and lists any repairs needed along the way. |
| `{module}_generation_trace.json` + `trace/` | Anyone checking the work | A complete record of how the week was produced (see below). |

The exercises work on files from your own run: a sample of your images, the vision pipeline's predictions (`results.csv`), and its metrics. The Python packages students need are listed in `exercises/requirements.txt`.

---

## How a Week Is Built

1. **Problem statement.** An AI "curriculum director" reads your week's description and learning outcomes, plus your run's results (accuracy, the hardest categories, sample successes and failures). It writes the week's problem, breaks it into three milestones, and spells out exactly which functions students will write. Each week also sees what earlier weeks covered, so it builds on them instead of repeating them.
2. **Tests first.** A second AI writes the unit tests from that specification, before any solution exists.
3. **Solution.** A third AI writes a reference solution that has to pass those tests.
4. **Checking and repair.** The solution and tests run together in an isolated sandbox on your real data. If a test fails, the failure is sent back to whichever AI wrote the faulty part. If it keeps failing, an independent **Arbiter**, an AI from a different model family, decides whether the tests, the solution or the original specification is wrong. If the specification is wrong, it is rewritten and the week is rebuilt.
5. **Starter code.** Only after every test passes is the student version made, by removing the solution's implementation and leaving guided `# TODO` steps.
6. **Slides.** The lecture slides are built last, from the verified solution and your run's results.

If a week cannot be made to pass its tests, no starter code or slides are made for it, so you never receive materials built on code that doesn't work. The other weeks still finish.

**The generation trace.** Every AI request and reply, every code version, every test run and every repair is saved in the week's `trace/` folder, with a fingerprint (SHA-256) of each file, and linked together in `{module}_generation_trace.json` using the W3C PROV standard. It shows exactly how each file came to be and which of your pipeline's outputs it was based on.

---

## The Lecture Slides

Each deck follows the same teaching order:

1. **Goal:** what the week produces, and a real number from your run that motivates it (for example, overall accuracy against the accuracy of the hardest category).
2. **Overview:** the whole week in one picture.
3. **Method:** one or more slides per technique, explained step by step.
4. **Why:** why the method works, and when it doesn't.
5. **Application:** the method applied to your data, with excerpts from the verified solution.
6. **Key takeaways.**

Charts and tables on the slides use only your run's real data; slide code that would invent data is rejected. Each slide is also rendered and checked from a screenshot by a vision-capable AI reviewer for overlapping, cut-off or unclear content, and a crowded slide is split in two rather than cut. Speaker notes are included.

---

## Writing Good Weeks

You describe each week in **Weekly Labs** on the **Curriculum Config** page (or under `modules` in the [YAML configuration](./YAML_CONFIG_GUIDE.md)). The AI follows your description closely, so:

- **Say what the week should teach, not just its topic.** "Extract texture (GLCM), color moment and lesion shape features to train classical machine learning baselines" produces a far more focused week than "Feature extraction".
- **Write two or three concrete learning outcomes** that start with a verb students can show: *calculate*, *train*, *compare*, *visualize*, *evaluate*.
- **Match the difficulty** (`beginner`, `intermediate`, `advanced`) to your students. A beginner week focuses on exploring data rather than training models.
- **Order the weeks** so each builds on the last: explore the data first, then features, then models, then explanation or deployment.
- **Mention your domain's terms** (e.g. "necrosis", "chlorosis") when they matter; the AI uses them in the handout and slides.

If you leave the weekly plan empty (and the topic fields blank), the AI plans a 6-week course for you, from data exploration through explainability to a final deployment week.

---

## Built-in Presets

The portal includes three ready-made courses to start from or adapt:

**Crop Leaf Disease Detection** (agricultural crop health, PlantVillage images)
1. Agricultural Imaging & Foliar Symptom Exploration
2. Handcrafted Morphological Descriptors & Baseline Classifiers
3. Self-Supervised Feature Embeddings with DINOv2
4. Zero-Shot Foliar Lesion Segmentation with SAM

**Skin Lesion Diagnostics** (dermatology)
1. NumPy Basics & Lesion Image Arrays
2. Pandas Diagnostic Analytics & Visualizations
3. PyTorch Lesion Classification Head
4. Interactive Lesion Outlining with SAM

**Culinary Dish Categorization** (food images)
1. Food Dataset Exploration & Color Profiling
2. PyTorch Deep Classifier for Dish Types
3. Portion Boundary Outlining with Foundation Models

---

## Using a Week in Class

A suggested flow for one week:

1. **Present** the slides; the speaker notes carry the explanation for each slide.
2. **Hand out** `{module}_overview.md`, `{module}_exercise.py`, `{module}_test.py` and the course's `requirements.txt`, together with the run's data files the exercise reads (from your output folder: `results.csv`, `run_summary.json`, `class_mapping.json` and the `images/` folder). Students keep them all in one folder.
3. **Students work through the milestones**, running `python -m pytest {module}_test.py` to check their progress. Tests fail until the matching milestone is complete.
4. **Review** with `{module}_solution.py`. To run the tests against it, change `{module}_exercise` to `{module}_solution` in the test file's import lines.

Read each week's handout and slides before teaching: the materials are AI-generated and checked by tests and reviewers, but you know your students and your subject best.
