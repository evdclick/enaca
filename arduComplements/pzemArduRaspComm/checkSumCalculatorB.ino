//Function to calculate checksum in 32byte array
byte checkSumCalculatorB(byte frameToCalcB[]) {
  byte checkSumStatus = 0;
  for (int checkAdder = 0; checkAdder < 31; checkAdder++) {
    checkSumStatus = checkSumStatus + frameToCalcB[checkAdder];
  }
  return checkSumStatus;
}