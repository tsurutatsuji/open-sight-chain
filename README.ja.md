# open-sight-chain

**機械が見た映像から、みんなで学ぶ。生の映像は誰にも渡さず、誰が何を出したかは書き換えられない記録に残す。**

[English](README.md)

> 状態：**ざっくりした試作（v0.0.1）**。アイデアを早く出すことを優先して公開しています。
> 設計は議論の対象です。大きく書き換える提案も歓迎します。

---

## 考え方

ロボット・車・スマホ・職場のカメラは毎日大量の映像を撮っています。しかし、ほとんどがAIの学習に使われていません。理由は3つです。

1. **生の映像は端末の外に出せない**（プライバシー・契約・通信量）
2. **データの出どころを証明できない**（買う側は信用できず、出す側は報酬をもらえない）
3. **悪いデータ・わざと壊すデータが混ざると見抜けない**

open-sight-chain は既にある3つの技術を組み合わせて、この3つを解きます。

| 問題 | 技術 | ここでの役割 |
|---|---|---|
| 生データを動かせない | **連合学習** | 各端末が手元で学習し、送るのはAIの数値（重み）だけ |
| 出どころを証明できない | **ハッシュでつないだ台帳** | 毎回、データの指紋・モデルの指紋・貢献度を記録。書き換えると検出される |
| 悪いデータが混ざる | **貢献度の採点** | 各端末の更新が全体を良くしたかを採点し、悪くしたものは除外 |

## 今動くもの

| 段階 | 部品 | ファイル | 状態 |
|---|---|---|---|
| 1 | 書き換えを検出できる台帳 | `osc/ledger.py` | ✅ 動作 |
| 2 | 複数ノードが同じ台帳を共有（最長の正しい鎖を採用） | `osc/node.py` | ✅ 動作 |
| 3 | 連合学習＋貢献度採点＋不正端末の除外 | `osc/fedlearn.py` | ✅ 動作（小さなモデル） |
| 4 | ブロックチェーン上の出どころ記録（スマートコントラクト） | `contracts/ProvenanceRegistry.sol` | 📐 設計の雛形 |
| 5 | 誰でも参加でき報酬が出る公開ネットワーク | — | 💡 未解決の課題 |

## 動かし方

```bash
git clone https://github.com/tsurutatsuji/open-sight-chain
cd open-sight-chain
pip install -r requirements.txt   # numpy のみ
python demo.py
python -m unittest -v
```

## 手伝ってほしいこと

[docs/ROADMAP.md](docs/ROADMAP.md) に一覧があります。主なもの：

- 小さなモデルを本物の画像AI（PyTorch / Flower）に置き換える
- HTTPでの同期を本物のP2P通信にする
- 不正に強い集計方法（Krum・トリム平均）
- 出どころ記録の契約をテスト用ネットに置く
- プライバシー強化（秘密集計・差分プライバシー）

[CONTRIBUTING.md](CONTRIBUTING.md) と [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) を読んで、Issue か Pull Request を出してください。

## 先行研究

組み合わせの新しさを主張するものではありません。土台：FedAvg（McMahan ほか 2017）、BlockFL（Kim ほか 2019）、Bittensor、Ocean Protocol、Flower。

## ライセンス

[Apache License 2.0](LICENSE)。プロジェクト名「open-sight-chain」の管理者は [@tsurutatsuji](https://github.com/tsurutatsuji)。
