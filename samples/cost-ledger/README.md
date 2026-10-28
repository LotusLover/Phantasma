# オフラインの仮想トークン費用計算

この小さなPythonサンプルは、記録済みのトークン数と**仮想単価**から、USD換算の費用を見積もります。実際の請求額や現在のprovider料金を示すものではありません。ネットワーク通信、APIキー、外部パッケージは使いません。

## 再現

Python 3.10以上を用意し、このフォルダーで実行します。

```text
python estimate.py usage.json rates.json
python -m unittest -v
```

サンプル入力は `usage.json` と `rates.json` です。出力には `HYPOTHETICAL FIXTURE` と `hypothetical_offline_estimate` が必ず含まれます。現在の fixture では入力100,000 tokens、うちcache 40,000、出力10,000、仮想単価を入力$1.50・cache $0.25・出力$6.00 / 1M tokens とし、推計値は $0.16 です。

## 計算

```text
((input_tokens - cached_input_tokens) * input_rate
 + cached_input_tokens * cached_input_rate
 + output_tokens * output_rate) / 1,000,000
```

cache tokenはinputの内数なので、input単価とcache単価を両方に重ねて課金しません。出力tokenの集計にreasoning tokenが含まれている場合も、別項目として二重加算しません。usageは非負整数、cache数はinput数以下、単価は有限な非負数である必要があります。金額計算は`Decimal`を使います。

実測請求と見積りは分けて記録してください。実測には対象期間のprovider明細と適用契約、通貨換算、割引、再試行、複数リクエストの扱いなど、ここにない情報が必要です。fixtureの値をproviderの料金として転用しないでください。

## ライセンス

同梱の `LICENSE-MIT-DRAFT.txt` は公開前レビュー用の草稿です。公開時に権利者・著作権年・対象範囲を確認してください。
