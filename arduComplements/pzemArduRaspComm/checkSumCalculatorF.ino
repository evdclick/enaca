//Function to calculate checksum in 8float array
float checkSumCalculatorF(float frameToCalcF[]) {
  float checkSumFloat = 0.0;
  for (int sumIndexer = 0; sumIndexer < 7; sumIndexer++) {
    checkSumFloat = checkSumFloat + frameToCalcF[sumIndexer];
  }
  return checkSumFloat;
}

