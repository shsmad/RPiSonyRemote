import math

from dataclasses import dataclass
from typing import Optional

# https://zerenesystems.com/cms/stacker/docs/tables/macromicrodof
# https://zerenesystems.com/cms/stacker/docs/dofcalculator


@dataclass
class DOFResult:
    step_size_suggested: float
    recommendation: str
    dof_classic: Optional[float] = None
    dof_optic: Optional[float] = None


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


def calculate_suggested_step_size(
    dof_classic: float = 0.0, dof_optic: float = 0.0, step_overlap: float = 0.0
) -> DOFResult:
    rec_DOF = dof_classic or 0.0
    if dof_optic and dof_optic > rec_DOF:
        rec_DOF = dof_optic

    frac = 1 - step_overlap if step_overlap else 1.0
    recommendation = ""

    if rec_DOF > 0:
        step_size_suggested = rec_DOF * frac
        if dof_classic and dof_optic:
            recommendation = "Aperture is near optimum for specified CoC"
            if dof_classic > dof_optic * 1.2:
                recommendation = (
                    "Resolution is limited by sensor or CoC setting, consider a narrower aperture or omit CoC"
                )

            elif dof_classic < dof_optic / 1.2:
                recommendation = "Resolution is limited by diffraction, consider a wider aperture"

    else:
        step_size_suggested = 0

    return DOFResult(step_size_suggested, recommendation, dof_classic, dof_optic)


def get_pupil_factor(pupil_ratio: Optional[float] = None) -> float:
    return pupil_ratio or 1.0
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


def calculate_effective_aperture(
    pupil_factor: float = 1.0, magnification: float = 0.0, lens_aperture: float = 0.0
) -> float:
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

    # pupil_factor = getPupilFactor()
    if lens_aperture:
        return lens_aperture * ((magnification or 0.0) / pupil_factor + 1.0)

    return lens_aperture


def calculate_classic_DOF(
    effective_fnumber: float = 0.0, magnification: float = 0.0, coc_width_mm: float = 0.0
) -> float:
    if effective_fnumber and magnification and coc_width_mm and magnification > 0.0:
        return 2 * coc_width_mm * effective_fnumber / magnification**2
    return 0.0


def calculate_wave_optics_DOF(effective_fnumber: float = 0.0, magnification: float = 0.0) -> float:
    #   const lensAperture = LensApertureField.value;
    #   const apertureType = LensApertureTypeField.value;
    #   const effectiveAperture = EffectiveFNumberField.value;
    #   const magnification = MagnificationField.value;

    if effective_fnumber and magnification and magnification > 0.0:
        NA = 1 / (2 * (effective_fnumber / magnification))
        dof_optic = getDOFFromNA(NA)
    else:
        dof_optic = 0.0

    return dof_optic
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


def calc(
    magnification: float,
    lens_aperture: float,
    coc_width_mm: Optional[float] = None,
    sensor_width: Optional[float] = None,
    sensor_width_px: Optional[float] = None,
    coc_width_px: Optional[float] = 3,
) -> Optional[DOFResult]:
    # usage 1: magnification + lens_aperture
    # usage 2: magnification + lens_aperture + coc_width_mm
    # usage 3: magnification + lens_aperture + sensor_width + sensor_width_px + coc_width_px
    if lens_aperture < 0 or magnification < 0:
        return None

    effective_fnumber = calculate_effective_aperture(
        pupil_factor=get_pupil_factor(), magnification=magnification, lens_aperture=lens_aperture
    )

    dof_optic = calculate_wave_optics_DOF(effective_fnumber=effective_fnumber, magnification=magnification)

    if sensor_width and sensor_width_px and coc_width_px:
        pixel_width = sensor_width / sensor_width_px
        coc_width_mm = pixel_width * coc_width_px

    if coc_width_mm:
        dof_classic = calculate_classic_DOF(
            effective_fnumber=effective_fnumber, magnification=magnification, coc_width_mm=coc_width_mm
        )
    else:
        dof_classic = 0.0

    return calculate_suggested_step_size(dof_classic=dof_classic, dof_optic=dof_optic, step_overlap=0)


if __name__ == "__main__":
    # CoC width = 3 * pixel_width = 3 * (sensor_width / sensor_width_px)
    print(calc(magnification=1.0, lens_aperture=5.6))

    print(calc(magnification=1.0, lens_aperture=5.6, coc_width_mm=0.03))
    print(calc(magnification=1.0, lens_aperture=5.6, coc_width_mm=0.0175))
    print(calc(magnification=1.0, lens_aperture=8, coc_width_mm=0.0175))

    print(calc(magnification=1.0, lens_aperture=5.6, sensor_width=35, sensor_width_px=6000, coc_width_px=3))
    print(calc(magnification=1.0, lens_aperture=8, sensor_width=35, sensor_width_px=6000, coc_width_px=3))
