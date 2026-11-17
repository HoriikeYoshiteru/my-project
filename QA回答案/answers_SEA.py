A = {}
A[('SEA',1)] = (
"""「対象外」には次の3種類があります。項目書（3DAA_SeA_Lv4複合_テスト項目書_v0.02）のテストケース_基本動作シートの備考欄に理由を記載しています。

(1) 3DAA_KH_SeA_0005／0007（定期送信300ms中に、イベントで同じALARM状態を再受信するケース）
　→ 複合(Lv4)では対象外です。異常系（信頼性：Lv5）で対応する項目のため、Lv5信頼性項目書側で実施してください。（備考欄に「信頼性」と記載）

(2) 3DAA_KH_SeA_0009／0010／0012／0013（SVT（Stolen Vehicle Tracking）実行中のALARM受信）
　→ 他機種(先行)の仕様のため、HC5.0(3DAA)では実施不要です。（HC5.0のSeAはACC/IG OFFの開始条件でのALARM通知のみ。車両位置のトラッキングは対象外）

(3) 3DAA_KH_SeA_0011／0014／0015／0018／0019（Privacy Setting／Subscription／ICB／DSSA・DSSS等の組合せ）
　→ 同じく他機種(先行)の仕様のため、HC5.0では実施不要です。

また、テスト項目_基本動作シートの実施要否欄の「対象外」は、「ALARM ONを検知すること」のように、後続ステップ（例：Send SeA Requestの送信）の確認で兼ねられるステップを指します。ケース自体を省略する意味ではなく、後続ステップが確認できていれば単独の確認は不要という意味です。""",
"""「对象外」分为以下三类，理由已写在用例表（テストケース_基本動作）的备注栏。

(1) 3DAA_KH_SeA_0005／0007（定期发送(300ms)期间，以事件方式再次收到相同ALARM状态）：复合(Lv4)中对象外，由异常系（可靠性Lv5）覆盖，请在Lv5可靠性项目书中实施。
(2) 3DAA_KH_SeA_0009／0010／0012／0013（SVT执行中收到ALARM）：属于其他机种（先行）的规格，HC5.0(3DAA)无需实施。
(3) 3DAA_KH_SeA_0011／0014／0015／0018／0019（Privacy Setting／Subscription／ICB／DSSA·DSSS等组合）：同样属于其他机种（先行）的规格，HC5.0无需实施。

另外，测试项目表实施要否栏的「对象外」是指该步骤可由后续步骤（如Send SeA Request的发送）一并确认，并非省略整个用例。""")

A[('SEA',2)] = (
"""ご質問の「TCU17_001～TCU016」は、項目書に旧管理番号として残っている「TCU17_0001～」の表記と思われます（3DAA_KH_SeA_F1_0005／0007の前提条件欄の記載で、3DAA_KH_SeA_F1_0001～0004、0006に対応する旧IDです）。ご提示のIDが別のものでしたらご指摘ください。

操作手順は、3DAA_SeA_Lv4複合_テスト項目書_v0.02の「テスト項目_基本動作」シートの手順列に記載のとおりです。実施対象（対象外でない）ケースの操作の要点は以下です。

・3DAA_KH_SeA_0001～0004（ALARM ON）：+B ON、セキュリティセット状態（Door Lock）で、ACC/IGの状態のみ変えて実施（0001：ACC-ON/IG-ON、0002：ACC-ON/IG-OFF、0003：ACC-OFF/IG-ON、0004：ACC-OFF/IG-OFF）。有効な位置情報を受信できる状態にする（取得できない場合はGPSジェネレータを使用）。CENTER（CANoe）からC_SCACTION（ALARM_BCM：1）を送信し、VSPからSecurity-Alert requestのresponse(Success)を返す。
・3DAA_KH_SeA_0006（ALARM OFF）：0004を実施後、C_SCACTION（ALARM_BCM：0）を送信。Security-Alert requestが送信されないこと。
・3DAA_KH_SeA_0008：0006のALARM_BCM：0送信から8sec後にALARM_BCM：1を送信。Security-Alert requestが送信されること。
・3DAA_KH_SeA_0017：0006のALARM_BCM：0送信から7sec以内にALARM_BCM：1を送信。ALARM ONを検知せず、送信されないこと。
・3DAA_KH_SeA_0016：+B OFF（OFFモード）でALARM_BCM：1を送信。Low Powerモードで動作してSeA送信後、OFFモードへ遷移すること。
・3DAA_KH_SeA_0020／0021：0001相当の条件で、位置情報が内部メモリにある場合（0020）／ない場合（0021：デフォルト位置情報）。

「対象外」のケース（0005、0007、0009～0015、0018、0019）は実施しないため、手順の提示は不要です。
なお、DAQデバッグログの設定手順は別途ご案内が必要なため、必要でしたら本チケットでお問い合わせください。""",
"""所问的「TCU17_001～TCU016」应为项目书中残留的旧管理编号「TCU17_0001～」（3DAA_KH_SeA_F1_0005／0007前提条件栏中的记载，对应3DAA_KH_SeA_F1_0001～0004、0006）。如您所指为其他ID，请告知。

操作步骤请见3DAA_SeA_Lv4复合_测试项目书_v0.02「テスト項目_基本動作」表的手顺列。实施对象用例的要点：
・0001～0004（ALARM ON）：+B ON、设防状态（Door Lock），仅改变ACC/IG状态（0001：ACC-ON/IG-ON，0002：ACC-ON/IG-OFF，0003：ACC-OFF/IG-ON，0004：ACC-OFF/IG-OFF）。确保可获取有效位置信息（无法获取时使用GPS发生器）。从CENTER（CANoe）发送C_SCACTION（ALARM_BCM：1），VSP返回Security-Alert request的response(Success)。
・0006：执行0004后发送ALARM_BCM：0，不发送Security-Alert request。
・0008：0006发送ALARM_BCM：0后8sec发送ALARM_BCM：1，发送Security-Alert request。
・0017：0006发送ALARM_BCM：0后7sec以内发送ALARM_BCM：1，不检测ALARM ON、不发送。
・0016：+B OFF（OFF mode）发送ALARM_BCM：1，以Low Power mode动作并发送SeA后迁移至OFF mode。
・0020／0021：与0001相同条件，内部存储器有位置信息（0020）／无位置信息（0021，使用默认位置信息）。

「对象外」用例（0005、0007、0009～0015、0018、0019）不实施，无需提供步骤。DAQ调试日志的设定方法需另行说明，如需要请在本工单咨询。""")
