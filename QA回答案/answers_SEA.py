A = {}
A[('SEA',1)] = (
"""「対象外」には次の3種類があります。項目書（3DAA_SeA_Lv4複合_テスト項目書_v0.02）のテストケース_基本動作シートの備考欄に理由を記載しています。

(1) 3DAA_KH_SeA_0005／0007（定期送信300ms中に、イベントで同じALARM状態を再受信するケース）
　→ 複合(Lv4)では対象外です。異常系（信頼性：Lv5）で対応する項目のため、Lv5信頼性項目書側で実施してください。（備考欄に「信頼性」と記載）

(2) 3DAA_KH_SeA_0009／0010／0012／0013（SVT実行中のALARM受信）、および0011／0014／0015／0018／0019（Privacy Setting／Subscription／ICB／DSSA・DSSS等の組合せ）
　→ HC5.0(3DAA)では実施不要です。3DAAの機能仕様（SeA）では、SeAの開始条件は「ALARM信号が not ON から ON へ変化したこと」のみで、Privacy Setting／SVT／Subscriptionによる開始条件は規定されていません。項目書の備考のとおり、他機種(先行)の仕様に基づく項目です。
　なお、SW SPEC（8B20Z3DA_H101 4.8.2 Table 58）には開始条件としてこれらが記載されていますが、3DAAの詳細仕様では適用されません。

また、テスト項目_基本動作シートの試験結果欄にある「対象外」は、「ALARM ONを検知すること」のように、後続ステップ（例：Send SeA Requestの送信）の確認で兼ねられるステップを指します（備考欄に理由を記載）。ケース自体を省略する意味ではありません。""",
"""「对象外」分为以下三类，理由已写在用例表（テストケース_基本動作）的备注栏。

(1) 3DAA_KH_SeA_0005／0007（定期发送(300ms)期间，以事件方式再次收到相同ALARM状态）：复合(Lv4)中对象外，由异常系（可靠性Lv5）覆盖，请在Lv5可靠性项目书中实施。
(2) 3DAA_KH_SeA_0009／0010／0012／0013（SVT执行中收到ALARM）及0011／0014／0015／0018／0019（Privacy Setting／Subscription／ICB／DSSA·DSSS等组合）：HC5.0(3DAA)无需实施。3DAA功能规格（SeA）中，SeA的启动条件仅为「ALARM信号由not ON变为ON」，未规定Privacy Setting／SVT／Subscription相关启动条件。如项目书备注所述，这些用例属于其他机种（先行）的规格。
　另外，SW SPEC（8B20Z3DA_H101 4.8.2 Table 58）中记载了这些条件，但不适用于3DAA的详细规格。

另外，测试项目表试验结果栏的「对象外」是指该步骤可由后续步骤（如Send SeA Request的发送）一并确认，并非省略整个用例。""")

A[('SEA',2)] = (
"""ご質問の「TCU17_001～TCU016」は、項目書に旧管理番号として残っている「TCU17_0001～」の表記と思われます（3DAA_KH_SeA_F1_0005／0007の前提条件欄の記載で、3DAA_KH_SeA_F1_0001～0004、0006に対応する旧IDです）。ご提示のIDが別のものでしたらご指摘ください。

操作手順は、3DAA_SeA_Lv4複合_テスト項目書_v0.02の「テスト項目_基本動作」シートの手順列に記載のとおりです。実施対象（対象外でない）ケースの操作の要点は以下です。

・3DAA_KH_SeA_0001～0004（ALARM ON）：+B ON、セキュリティセット状態（Door Lock）で、ACC/IGの状態のみ変えて実施（0001：ACC-ON/IG-ON、0002：ACC-ON/IG-OFF、0003：ACC-OFF/IG-ON、0004：ACC-OFF/IG-OFF）。有効な位置情報を受信できる状態にする（取得できない場合はGPSジェネレータを使用）。CENTER（CANoe）からC_SCACTION（ALARM_BCM：1）を送信し、VSPからSecurity-Alert requestのresponse(Success)を返す。
・3DAA_KH_SeA_0006（ALARM OFF）：0004を実施後、C_SCACTION（ALARM_BCM：0）を送信。Security-Alert requestが送信されないこと。
・3DAA_KH_SeA_0008：0006のALARM_BCM：0送信から8sec後にALARM_BCM：1を送信。Security-Alert requestが送信されること。
・3DAA_KH_SeA_0017：0006のALARM_BCM：0送信から7sec以内にALARM_BCM：1を送信。ALARM ONを検知せず、送信されないこと。（3DAA機能仕様 4.8(d)：ALARM=OFFが7秒以上継続したら盗難状態をOFF（警報なし）に戻す。7秒未満のOFF→ONは無視）
・3DAA_KH_SeA_0016：+B OFF（OFFモード）でALARM_BCM：1を送信。項目書の期待動作はLow Powerモードで動作しSeA送信後にOFFモードへ遷移ですが、SPEC（H102 4.9.6）では、OFFモードでALARMを検知してSeAを開始した場合は、処理完了後にOFFモードへ戻ると規定されています。経由モードの詳細はサプライヤ実装に依存するため、動作結果を見て確認します。
・3DAA_KH_SeA_0020／0021：0001相当の条件で、位置情報が内部メモリにある場合（0020）／ない場合（0021）。位置情報が取得できていない場合、3DAA機能仕様 4.8 Abnormal(d) では全て0のデータを送信します。送信失敗時のリトライは3秒周期×3回です（4.8 Table 82 No.8）。

「対象外」のケース（0005、0007、0009～0015、0018、0019）は実施しないため、手順の提示は不要です。
なお、DAQデバッグログの設定手順は別途ご案内が必要なため、必要でしたら本チケットでお問い合わせください。""",
"""所问的「TCU17_001～TCU016」应为项目书中残留的旧管理编号「TCU17_0001～」（3DAA_KH_SeA_F1_0005／0007前提条件栏中的记载，对应3DAA_KH_SeA_F1_0001～0004、0006）。如您所指为其他ID，请告知。

操作步骤请见3DAA_SeA_Lv4复合_测试项目书_v0.02「テスト項目_基本動作」表的手顺列。实施对象用例的要点：
・0001～0004（ALARM ON）：+B ON、设防状态（Door Lock），仅改变ACC/IG状态（0001：ACC-ON/IG-ON，0002：ACC-ON/IG-OFF，0003：ACC-OFF/IG-ON，0004：ACC-OFF/IG-OFF）。确保可获取有效位置信息（无法获取时使用GPS发生器）。从CENTER（CANoe）发送C_SCACTION（ALARM_BCM：1），VSP返回Security-Alert request的response(Success)。
・0006：执行0004后发送ALARM_BCM：0，不发送Security-Alert request。
・0008：0006发送ALARM_BCM：0后8sec发送ALARM_BCM：1，发送Security-Alert request。
・0017：0006发送ALARM_BCM：0后7sec以内发送ALARM_BCM：1，不检测ALARM ON、不发送。（3DAA功能规格4.8(d)：ALARM=OFF持续7秒以上才恢复为无警报，不足7秒的OFF→ON被忽略）
・0016：+B OFF（OFF mode）发送ALARM_BCM：1。项目书期望为Low Power mode动作并发送SeA后迁移至OFF mode，SPEC（H102 4.9.6）规定：在OFF mode检测到ALARM并开始SeA时，处理完成后返回OFF mode。经由的模式取决于供应商实现，需根据实际动作确认。
・0020／0021：与0001相同条件，内部存储器有位置信息（0020）／无位置信息（0021）。未获取到位置信息时，按3DAA功能规格4.8 Abnormal(d)上传全0数据。发送失败重试为3秒周期×3次（4.8 Table 82 No.8）。

「对象外」用例（0005、0007、0009～0015、0018、0019）不实施，无需提供步骤。DAQ调试日志的设定方法需另行说明，如需要请在本工单咨询。""")
