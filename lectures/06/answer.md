# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：
    - app.agent： search_materials、make_quiz、save_learning_log
    - app.mcp_agent： glossary_search_glossary
- STEP 2 の [tool call]： glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]： fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：
    - aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 バージョニング 概要'})
    - aws_aws___search_documentation({'search_phrase': 'Using versioning in S3 buckets overview', 'topics': ['general']})
- 気づき・疑問：
    - `app.agent` は直接実装したものツールとして認識し、`app.mcp_agent` は設定したサーバのツールが認識できる
    - 設定にサーバを追加するだけでツールを増やすことができている
        - fetch 追加後は2個、aws 追加後は7個
    - glossary と fetch はコマンドで自分の環境が起動し、aws は `https://knowledge-mcp.global.api.aws` へ接続している
    - STEP2 と STEP3 は1回目にツールを呼び、2回目に結果を答えているが、STEP 4 は `aws_aws___search_documentation` を2回呼んでから答えている(1回目の日本語の検索語では回答できず、2回目の英語の検索語で取得している)

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎
- やったこと：MCPサーバに `get_lecture_summary` を公開する
- 結果：
    - `app.mcp_agent --list-tools` を実行し、 `glossary_get_lecture_summary` が追加されていることを確認
    - 「第2回では何を学びますか？」の質問に対する動作：
        - [tool call] は `glossary_get_lecture_summary({'lecture': 2})` で、[tool call] は  `glossary_get_lecture_summary -> # 第2回 ファインチューニングとLoRA`
        - 講義の要点を返しており、事前学習とファインチューニングの違い、SFT、PEFT と LoRA、QLoRA との関係、Google Colab での演習、に対して回答していた
- 気づき・疑問：
    - サーバ側で関数を公開するだけで、エージェント側のプログラムを書き換えなくてもツールがt買えるようになっていた
    - 質問に対して、今回追加したツールが最初から選択されており、他のツールを呼び出すことはなかった
    - どのツールでも該当するような質問をすると、別のツールが呼ばれるのか、その閾値はどうなっているのかが気になる
