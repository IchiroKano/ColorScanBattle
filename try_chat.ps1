$jsonData = @'
{
  "output_type": "chat",
  "input_type": "chat",
  "input_value": "こんにちは",
  "session_id": "YOUR_SESSION_ID_HERE"
}
'@

curl.exe --request POST `
  --url "http://razpi00.local:7860/api/v1/run/06dce709-8745-4275-a63e-e5a64c976e74?stream=false" `
  --header "Content-Type: application/json" `
  --header "x-api-key: sk-ySAlois_p3dpXTPP6B6h8SiUCGTsJKEHgRB-W4GwnGU" `
  --data $jsonData
