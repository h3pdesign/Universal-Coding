# Contributing to Microsoft Learning Repositories

MCT contributions are a key part of keeping the lab and demo content current as the Azure platform changes. We want to make it as easy as possible for you to contribute changes to the lab files. Here are a few guidelines to keep in mind as you contribute changes.

## GitHub Use & Purpose

Microsoft Learning uses GitHub to publish lab steps and lab scripts for courses that cover cloud services like Azure. Use GitHub for content changes, fixes, and improvements to the labs — not for general course prep discussion.

- When preparing to teach, download the latest lab files from GitHub rather than linking students directly to repository files in-class.
- Prefer the GitHub Pages site for public-facing lab instructions: <https://microsoftlearning.github.io/mslearn-azure-ml/>

## How to contribute

- Fork the repository and open a small, focused PR against `main`.
- Provide a short reproduction/validation checklist in the PR description.
- If a change affects billing, permissions, or requires new Azure resources, document those implications in the PR.

## Notebooks and scripts

- Keep notebooks runnable: preserve top cells that perform data loading and preprocessing when converting notebooks to scripts.
- Show required environment variables and provide example export commands or a sample `.env` in the lab README.

## Azure & secrets

- Never commit secrets, keys, or connection strings. Use environment variables and placeholders in templates.
- When adding ARM/Bicep/CLI templates, document required permissions and any potential billing impact.

## Validation

- Manual validation is expected: open the notebook and run affected cells in `jupyter lab`.
- For automated or CI checks, consider `papermill` to execute notebooks headlessly and include the sample command in the PR.

## Reviewer checklist

When reviewing a PR, verify:

- [ ] No secrets, keys, or credentials committed (check for `.env` placeholders instead).
- [ ] Notebooks run without errors in `jupyter lab`; preprocessing cells are at the top.
- [ ] Lab README or inline docs document required environment variables.
- [ ] PR description includes validation steps or a reproduction checklist.
- [ ] If Azure resources added: permissions and billing implications are documented.
- [ ] Changes are scoped to the relevant lab or feature folder.

## Additional resources

- MCT user guide: <https://microsoftlearning.github.io/MCT-User-Guide/>

If you have a larger proposal or structural change, open an issue first to discuss the approach before submitting a large PR.
