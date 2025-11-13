//Function to check if voltage is present in pzem module after frame consulting
byte voltageDetect(float framElement) {
  if (framElement == -3) {
    return (disabled);  //Clear status bit energyzed in order to prevent unnecesary reading from raspberry
  } else {
    return (enabled);  //set status bit energyzed in order to be read from raspberry
  }
}
