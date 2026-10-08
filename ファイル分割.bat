@echo off

rem ****基本設定****
rem 分割後のファイルの最大サイズ(バイト)。40000000=約40MB
rem 2GBを超えるファイルも分割できます(CAB形式の2GB制限は受けません)
set fragmentsize=40000000
set fragmentsize2=約40MB
rem ****************

rem 引数があるか確認する
if "%~1"=="" (
 goto noarg
) else (
 goto main
)

rem 引数が無い場合
:noarg
echo 分割したいファイルを「ファイル分割.bat」へドラッグ＆ドロップしてください。
echo 処理を終了します。何かキーを押して下さい。
pause
goto end

rem 引数がある場合
:main
rem バッチファイルのパスへ移動
cd /d "%~dp0"

rem フォルダ作成用の日付を生成
set time_tmp=%time: =0%
set dirname=%date:/=%%time_tmp:~0,2%%time_tmp:~3,2%%time_tmp:~6,2%

rem 分割元ファイル名を取得
set filename=%~nx1
set fragmentfilename=%filename%.????

rem ハッシュ値を確認
for /f "usebackq skip=1 delims=" %%A in (`certutil -hashfile "%~f1"`) do (
    set hash_before=%%A
    goto exitfor
)
:exitfor

echo %hash_before%

rem 実行確認
echo 分割前ファイル名：%filename%
echo 分割後ファイル名：%fragmentfilename%
echo 出力先　　　　　：%~dp0%dirname%
echo 分割サイズ　　　：%fragmentsize2%
echo ハッシュ値　　　：%hash_before%
set /p yn_check="ファイル分割を開始しますか？(y/n)"

if /i "%yn_check%"=="y" (
 goto yes
) else (
 goto end
)

:yes

echo -------------------------------------
echo;
mkdir "%~dp0%dirname%"

rem 分割を実行(PowerShellでバイナリを固定サイズに分割)
set "SPLIT_SRC=%~f1"
set "SPLIT_DST=%~dp0%dirname%"
set "SPLIT_SIZE=%fragmentsize%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$src=$env:SPLIT_SRC; $dst=$env:SPLIT_DST; $name=[IO.Path]::GetFileName($src); $max=[long]$env:SPLIT_SIZE; $in=[IO.File]::OpenRead($src); $buf=New-Object byte[] 4MB; $i=1; try { while($in.Position -lt $in.Length){ $o=[IO.File]::Create((Join-Path $dst ($name+'.'+$i.ToString('0000')))); $w=0L; while($w -lt $max){ $r=[Math]::Min([long]$buf.Length,$max-$w); $k=$in.Read($buf,0,[int]$r); if($k -le 0){break}; $o.Write($buf,0,$k); $w+=$k }; $o.Close(); $i++ } } finally { $in.Close() }"
if errorlevel 1 goto fail

set output=%~dp0%dirname%\ファイル結合.bat
rem 結合用バッチファイル作成
>"%output%" echo @echo off
>>"%output%" echo cd /d "%%~dp0"
>>"%output%" echo set "filename=%filename%"
>>"%output%" echo set "hash_before=%hash_before%"
>>"%output%" echo echo %filename%の結合を開始します。
>>"%output%" echo powershell -NoProfile -ExecutionPolicy Bypass -Command "$n=$env:filename; $d=(Get-Location).Path; $parts=@([IO.Directory]::GetFiles($d) -match ([regex]::Escape($n)+'\.\d{4}$')); if($parts.Count -eq 0){exit 1}; [Array]::Sort($parts); $o=[IO.File]::Create((Join-Path $d $n)); $buf=New-Object byte[] 4MB; foreach($p in $parts){ $s=[IO.File]::OpenRead($p); while(($k=$s.Read($buf,0,$buf.Length)) -gt 0){ $o.Write($buf,0,$k) }; $s.Close() }; $o.Close()"
>>"%output%" echo if errorlevel 1 goto fail
>>"%output%" echo echo 結合が完了しました。
>>"%output%" echo echo ハッシュ値チェックを開始します。
>>"%output%" echo echo;
>>"%output%" echo for /f "usebackq skip=1 delims=" %%%%A in (`certutil -hashfile "%%filename%%"`) do (
>>"%output%" echo     set hash_after=%%%%A
>>"%output%" echo     goto exitfor2
>>"%output%" echo )
>>"%output%" echo :exitfor2
>>"%output%" echo echo -------------------------------------
>>"%output%" echo echo 分割前ハッシュ値：%%hash_before%%
>>"%output%" echo echo 結合後ハッシュ値：%%hash_after%%
>>"%output%" echo echo -------------------------------------
>>"%output%" echo if "%%hash_before%%"=="%%hash_after%%" (
>>"%output%" echo     echo ハッシュ値が一致しました。終了します。
>>"%output%" echo ) else (
>>"%output%" echo     echo ハッシュ値に差異があります。ファイル分割・結合どちらかが失敗しています。
>>"%output%" echo )
>>"%output%" echo pause
>>"%output%" echo exit /b
>>"%output%" echo :fail
>>"%output%" echo echo 分割ファイルが見つからないか、結合に失敗しました。
>>"%output%" echo pause

rem 分割フォルダを開く
start "" "%~dp0%dirname%"
echo;
echo -------------------------------------
echo ファイル分割が完了しました。終了します。
pause
goto end

:fail
echo ファイル分割に失敗しました。
pause

:end
