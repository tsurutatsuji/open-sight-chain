# Contributing

Thanks for looking. This project is an early sketch; big changes are welcome.

## How to contribute

1. Look at [docs/ROADMAP.md](docs/ROADMAP.md), open issues, or this week's **Paper watch** issue (new papers to bring into the code).
2. For large changes, open an issue first to discuss the direction.
3. Fork, branch, change, and run the tests:
   ```bash
   python -m unittest -v
   python demo.py
   ```
4. Open a pull request describing **what** changed and **why**.

## Rules

- Keep the core readable. A newcomer should understand each file in one sitting.
- Every behavior change comes with a test.
- Heavy dependencies (PyTorch, Flower, web3) go behind optional extras, not into the core.

## Sign-off (DCO)

Sign your commits to certify you wrote the change and can submit it under the project license
([Developer Certificate of Origin](https://developercertificate.org/)):

```bash
git commit -s -m "your message"
```

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE).

日本語での Issue・PR も歓迎します。
