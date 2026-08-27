---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-27T00:00:00+09:00
---
# QuickモデルBenchmarkの実行記録

2026-08-27に`quick-basic`をLuna、Terra、Solで各1回実行した。全candidateのdeterministic validationはPASSだった。固定Luna Judgeによるblind評価は、LunaがcompletenessとprovenanceでFAIL、TerraとSolが6観点すべてPASSだった。

Actor input/output/total tokenは、subagent実行インターフェースが実測usageを返さなかったため、全candidateで`unavailable`として保存した。文字数等による推定は行わなかった。
