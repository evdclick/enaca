//Function definition to get data from energy modules pzem004t installed in the same bus. Code efficiency
void pzemGetter(float frmEnergy[], PZEM004Tv30 pzemModule, byte statusFlagger[], byte busyFlagLocator) {
  statusFlagger[busyFlagLocator] = enabled;
  frmEnergy[0] = 11.07;  //I added this one as a personal initial element verification in raspberry
  frmEnergy[1] = pzemModule.voltage();
  if (isnan(frmEnergy[1]) || (frmEnergy[1] > 500)) {  //Validating voltage value in case of power off or bigger than expected
    frmEnergy[1] = -3.0;
  }
  //If there's no voltage then avoid requesting the rest of variables
  if (frmEnergy[1] == -3.0) {
    frmEnergy[2] = -3.0;
    frmEnergy[3] = -3.0;
    frmEnergy[4] = -3.0;
    frmEnergy[5] = -3.0;
    frmEnergy[6] = -3.0;
    frmEnergy[7] = 26.10;  //I added this one as a personal final element verification in raspberry
    statusFlagger[busyFlagLocator] = disabled;
    return;
  }
  frmEnergy[2] = pzemModule.power();
  if ((isnan(frmEnergy[2])) || (frmEnergy[3] > 4000)) {  //Validating power value in case of power off or bigger than expected for 110VAC
    frmEnergy[2] = -3.0;
  }
  frmEnergy[3] = pzemModule.current();
  if ((isnan(frmEnergy[3])) || (frmEnergy[3] > 100)) {  //Validating voltage value in case of power off or bigger than max amperage pzem004t
    frmEnergy[3] = -3.0;
  }
  frmEnergy[4] = pzemModule.energy();
  if ((isnan(frmEnergy[4])) || (frmEnergy[4] > 2000)) {  //Validating energy value in case of power off or bigger than expected
    frmEnergy[4] = -3.0;
  }
  frmEnergy[5] = pzemModule.frequency();
  if ((isnan(frmEnergy[5])) || (frmEnergy[5] > 100)) {  //Validating frecuency value in case of power off or bigger than expected
    frmEnergy[5] = -3.0;
  }
  frmEnergy[6] = pzemModule.pf();
  if ((isnan(frmEnergy[6])) || (frmEnergy[6] > 2)) {  //Validating pf value in case of power off or bigger than expected
    frmEnergy[6] = -3.0;
  }
  frmEnergy[7] = 0.0;  // Will be used for checkSumFloat before serial transmission
  statusFlagger[busyFlagLocator] = disabled;
}
