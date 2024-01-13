import math

# https://zerenesystems.com/cms/stacker/docs/tables/macromicrodof
# https://zerenesystems.com/cms/stacker/docs/dofcalculator


def getDOFFromNA(NA: float) -> float:
    # NA is the subject-side numerical aperture
    # for reference see https://www.photomacrography.net/forum/viewtopic.php?p=124722#p124722
    DOF = 0.0
    if NA <= 1.0:
        macro_lambda = 0.00055  # mm for green light
        refractive_index = 1.0
        DOF = (
            2
            * macro_lambda
            / (4 * refractive_index * (1 - math.sqrt(1 - (NA / refractive_index) * (NA / refractive_index))))
        )

    return DOF


class MacroCalculator:
    sensor_width = 0.0
    subject_width = 0.0
    magnification = 1.0
    lens_aperture = 0.0
    pupil_ratio = 1.0
    effective_fnumber = 0.0
    sensor_width_px = 0.0
    pixel_width = 0.0
    coc_width_px = 3.0
    coc_width_mm = 0.0
    dof_classic = 0.0
    dof_optic = 0.0
    step_overlap = 0.0
    step_size_suggested = 0.0
    recommendation = ""

    def getPupilFactor(self) -> float:
        return self.pupil_ratio or 1.0
        #   const pupilRatioType = PupilRatioTypeField.value;
        #   const pupilRatio = PupilRatioField.value;
        #   let pupilFactor = 1.0;
        #   if (hasValue(pupilRatio)) {
        #     pupilFactor = pupilRatio;
        #     if (pupilRatioType == "FrontOverRear") {
        #       pupilFactor = 1.0/pupilFactor;
        #     }
        #   }
        #   return pupilFactor;

    def calculateEffectiveAperture(self) -> None:
        #   const lensAperture = LensApertureField.value;
        #   const apertureType = LensApertureTypeField.value;
        #   const magnification = MagnificationField.value;
        #   if (apertureType == "NA") {
        #     if (hasValue(lensAperture) && lensAperture > 0.0 && hasValue(magnification)) {
        #       const NA = lensAperture;
        #       setFieldValue(EffectiveFNumberField,magnification/(2*NA));
        #       EffectiveFNumberSet();
        #     }
        #   } else if (apertureType == "EffectiveFNumber") {
        #     if (hasValue(lensAperture)) {
        #       setFieldValue(EffectiveFNumberField,lensAperture);
        #       EffectiveFNumberSet();
        #     }
        #   } else { // assume normal F-number
        pupil_factor = self.getPupilFactor()
        if self.lens_aperture:
            mag = self.magnification or 0.0
            self.effective_fnumber = self.lens_aperture * (mag / pupil_factor + 1.0)
            self.EffectiveFNumberSet()

    def SensorWidthSet(self) -> None:
        self.calculateMagnification()
        self.calculateSubjectWidth()
        self.calculatePixelWidth()

    def SubjectWidthSet(self) -> None:
        self.calculateMagnification()

    def MagnificationSet(self) -> None:
        self.calculateSubjectWidth()
        self.calculateEffectiveAperture()
        self.calculateClassicDOF()

    def LensApertureSet(self) -> None:
        self.calculateEffectiveAperture()
        self.calculateWaveOpticsDOF()

    def PupilRatioSet(self) -> None:
        self.calculateEffectiveAperture()

    def EffectiveFNumberSet(self) -> None:
        self.calculateClassicDOF()
        self.calculateWaveOpticsDOF()

    def SensorWidthPixelsSet(self) -> None:
        self.calculatePixelWidth()

    def PixelWidthSet(self) -> None:
        self.calculateCOCWidth()

    def calculatePixelWidth(self) -> None:
        if self.sensor_width and self.sensor_width_px:
            self.pixel_width = self.sensor_width / self.sensor_width_px
            self.PixelWidthSet()

    def CoCWidthPixelsSet(self) -> None:
        self.calculateCOCWidth()

    def calculateCOCWidth(self) -> None:
        if self.pixel_width and self.coc_width_px:
            self.coc_width_mm = self.pixel_width * self.coc_width_px
            self.CoCWidthmmSet()

    def CoCWidthmmSet(self) -> None:
        if not self.coc_width_mm:
            self.dof_classic = 0
            self.DOFClassicSet()
            self.calculateSuggestedStepSize()

        self.calculateClassicDOF()

    def calculateClassicDOF(self) -> None:
        if self.effective_fnumber and self.magnification and self.coc_width_mm and self.magnification > 0.0:
            self.dof_classic = (
                2 * self.coc_width_mm * self.effective_fnumber / (self.magnification * self.magnification)
            )
            self.DOFClassicSet()

    def DOFClassicSet(self) -> None:
        self.calculateSuggestedStepSize()

    def calculateWaveOpticsDOF(self) -> None:
        #   const lensAperture = LensApertureField.value;
        #   const apertureType = LensApertureTypeField.value;
        #   const effectiveAperture = EffectiveFNumberField.value;
        #   const magnification = MagnificationField.value;

        if self.effective_fnumber and self.magnification and self.magnification > 0.0:
            NA = 1 / (2 * (self.effective_fnumber / self.magnification))
            self.dof_optic = getDOFFromNA(NA)
        else:
            self.dof_optic = 0

        self.DOFWaveOpticsSet()
        # if (hasValue(lensAperture) && apertureType == "NA") {
        #     const NA = lensAperture;
        #     setDOFWaveOptics(getDOFFromNA(NA));
        # } else if (hasValue(effectiveAperture) && hasValue(magnification)) {
        #     if (magnification > 0.0) {
        #         const feff = effectiveAperture;
        #         const NA = 1/(2*(feff/magnification));
        #         setDOFWaveOptics(getDOFFromNA(NA));
        #     }
        # } else {
        #     setDOFWaveOptics("");
        # }

    def DOFWaveOpticsSet(self) -> None:
        # autoAdvance = false;
        self.calculateSuggestedStepSize()

    def StepOverlapSet(self) -> None:
        self.calculateSuggestedStepSize()

    def calculateSuggestedStepSize(self) -> None:
        recDOF = self.dof_classic or 0.0
        if self.dof_optic and self.dof_optic > recDOF:
            recDOF = self.dof_optic

        frac = 1 - self.step_overlap if self.step_overlap else 1.0
        self.recommendation = ""

        if recDOF > 0:
            self.step_size_suggested = recDOF * frac
            if self.dof_classic and self.dof_optic:
                self.recommendation = "Aperture is near optimum for specified CoC"
                if self.dof_classic > self.dof_optic * 1.2:
                    self.recommendation = (
                        "Resolution is limited by sensor or CoC setting, consider a narrower aperture or omit CoC"
                    )

                elif self.dof_classic < self.dof_optic / 1.2:
                    self.recommendation = "Resolution is limited by diffraction, consider a wider aperture"

        else:
            self.step_size_suggested = 0
        self.StepSizeSuggestedSet()

    def StepSizeSuggestedSet(self) -> None:
        pass

    def calculateMagnification(self) -> None:
        if self.sensor_width and self.subject_width and self.subject_width > 0.0:
            oldmag = self.magnification
            newmag = self.sensor_width / self.subject_width
            # fuzz to avoid recursion
            if oldmag == 0.0 or abs(1.0 - newmag / oldmag) > 0.0001:
                self.magnification = newmag
                self.MagnificationSet()

    def calculateSubjectWidth(self) -> None:
        if self.sensor_width and self.magnification and self.magnification > 0:
            oldSubjectWidth = self.subject_width
            newSubjectWidth = self.sensor_width / self.magnification
            # avoid recursion
            if oldSubjectWidth == 0 or abs(1.0 - newSubjectWidth / oldSubjectWidth) > 0.0001:
                self.subject_width = newSubjectWidth
                self.SubjectWidthSet()

    def Refresh(self) -> None:
        self.SensorWidthSet()
        self.SubjectWidthSet()
        self.MagnificationSet()
        self.LensApertureSet()
        # self.LensApertureTypeSet()
        self.PupilRatioSet()
        # self.PupilRatioTypeSet()
        self.EffectiveFNumberSet()
        self.SensorWidthPixelsSet()
        self.PixelWidthSet()
        self.CoCWidthPixelsSet()
        self.CoCWidthmmSet()
        self.DOFClassicSet()
        self.DOFWaveOpticsSet()
        self.StepOverlapSet()
        self.StepSizeSuggestedSet()
        # self.EvaluationTextSet()

    def calc(self, magnification: float, lens_aperture: float) -> tuple[float, str]:
        self.set_magnification_and_aperture(magnification, lens_aperture)
        return (self.step_size_suggested, self.recommendation)

    def calc2(self, magnification: float, lens_aperture: float, coc_width_mm: float) -> tuple[float, str]:
        self.set_magnification_and_aperture(magnification, lens_aperture)
        self.coc_width_mm = coc_width_mm
        self.CoCWidthmmSet()
        return (self.step_size_suggested, self.recommendation)

    def calc3(
        self,
        magnification: float,
        lens_aperture: float,
        sensor_width: float,
        sensor_width_px: float,
        coc_width_px: float,
    ) -> tuple[float, str]:
        self.set_magnification_and_aperture(magnification, lens_aperture)
        self.sensor_width = sensor_width
        self.SensorWidthSet()
        self.sensor_width_px = sensor_width_px
        self.SensorWidthPixelsSet()
        self.coc_width_px = coc_width_px
        self.CoCWidthPixelsSet()
        return (self.step_size_suggested, self.recommendation)

    def set_magnification_and_aperture(self, magnification: float, lens_aperture: float) -> None:
        self.magnification = magnification
        self.MagnificationSet()
        self.lens_aperture = lens_aperture
        self.LensApertureSet()


if __name__ == "__main__":
    # CoC width = 3 * pixel_width = 3 * (sensor_width / sensor_width_px)
    calc = MacroCalculator()
    print(calc.calc(magnification=1.0, lens_aperture=5.6))

    print(calc.calc2(magnification=1.0, lens_aperture=5.6, coc_width_mm=0.03))
    print(calc.calc2(magnification=1.0, lens_aperture=5.6, coc_width_mm=0.0175))
    print(calc.calc2(magnification=1.0, lens_aperture=8, coc_width_mm=0.0175))

    print(calc.calc3(magnification=1.0, lens_aperture=5.6, sensor_width=35, sensor_width_px=6000, coc_width_px=3))
    print(calc.calc3(magnification=1.0, lens_aperture=8, sensor_width=35, sensor_width_px=6000, coc_width_px=3))
