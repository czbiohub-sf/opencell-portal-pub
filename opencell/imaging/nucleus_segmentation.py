import numpy as np
from scipy import ndimage
import skimage

from opencell.imaging import utils


def generate_final_mask(im):
    '''
    High-level method to generate the final nucleus segmentation mask
    '''

    # generate an initial, crude background mask
    background_mask = generate_background_mask(im, sigma=5, rel_thresh=1.0)

    # refine the crude mask
    refined_background_mask, _, _ = refine_background_mask(
        im,
        background_mask,
        sigma=4,
        radius=5,
        percentile=7,
        max_area=1e4,
        min_area=900,
    )

    # remove regions too small to be a nucleus from the refined mask
    refined_background_mask = utils.remove_small_regions(refined_background_mask, min_area=1000)

    # generate the (labeled) watershed mask
    watershed_mask = generate_watershed_mask(refined_background_mask, min_distance=15)

    # remove watershed regions that touch the edge of the image,
    # because they are often not accurately segmented
    watershed_mask = utils.remove_edge_regions(watershed_mask)

    return watershed_mask


def generate_background_mask(im, sigma, rel_thresh):
    '''
    Generate a crude nucleus background mask using Li thresholding
    '''
    # smooth the raw image
    imf = skimage.filters.gaussian(im, sigma=sigma)

    # background mask from minimum cross-entropy
    thresh = rel_thresh * skimage.filters.threshold_li(imf)
    mask = imf > thresh
    mask = skimage.morphology.erosion(mask)
    return mask


def laplacian_of_gaussian_filter(im, sigma):
    '''
    Laplace transform a Gaussian-smoothed image
    (aka the Laplacian-of-Gaussian or LoG filter)
    '''
    imf = skimage.filters.gaussian(im, sigma=sigma)
    im_lg = skimage.filters.laplace(imf, ksize=3)
    return im_lg


def refine_background_mask(
    im, background_mask, sigma, radius, percentile, max_area, min_area
):
    '''
    im : raw nucleus image
    background_mask : 'crude' background mask generated by generate_background_mask
    sigma : radius of gaussian for smoothing
    radius : size of the disk for the closing operation
    percentile : intensity threshold for the local minima mask
    max_area : maximum area of holes to fill
    min_area : minimum area of region in the local minimum mask to remove from the background mask

    Steps
    1) generate a 'refined' background mask by thresholding the laplace transform at zero
    2) morphologically close this mask and fill holes to eliminate intra-nuclear holes or gaps
       (empirically, this requires a closing disk of radius at least 4)
    3) multiply this 'refined' mask by the existing background mask (`background_mask`)
       to restore any 'true' holes/gaps that were present in the background mask
    4) generate a mask of local minima in the laplace transform,
       using a percentile threshold (5%-7% works well)
    5) iterate over regions in this local-minima mask and remove them from the refined mask
       if they partially overlap with the background of the refined mask

    This procedure helps to capture the narrow regions and gaps between clumped nuclei,
    which dramatically improves the accuracy of the nucleus positions
    extracted from the distance-transformed mask.

    An alternative and likely better approach would be to find a more sophisticated way
    of 'filling in' the interiors of the nuclei in the refined background mask;
    the use of closing followed by hole-filling here is so crude that the hackish use
    of the local minima mask to add back real gaps between nuclei becomes necessary
    to meaningfully improve over the crude `background_mask`.

    '''

    im_lg = laplacian_of_gaussian_filter(im, sigma)
    refined_mask = (im_lg > 0) * background_mask

    # eliminate intra-nuclear holes in the mask
    refined_mask = skimage.morphology.closing(refined_mask, skimage.morphology.disk(radius))
    refined_mask = skimage.morphology.remove_small_holes(
        refined_mask, area_threshold=max_area, connectivity=1
    )

    # multiply the mask by the background mask again to retain any holes that were present
    # in the background mask (which we can assume are real)
    refined_mask *= background_mask

    # create a mask of local minima in the LoG image
    minima_mask = im_lg < np.percentile(im_lg, percentile)

    # remove regions in the minima mask from the refined mask
    # if they partially overlap with the background of the refined mask
    minima_mask_labeled = skimage.measure.label(minima_mask, connectivity=1)
    props = skimage.measure.regionprops(minima_mask_labeled)
    for prop in props:
        region_overlaps_background = np.min(refined_mask[prop.coords[:, 0], prop.coords[:, 1]]) == 0
        if region_overlaps_background or prop.area > min_area:
            refined_mask[prop.coords[:, 0], prop.coords[:, 1]] = False

    return refined_mask, minima_mask, im_lg


def find_region_centers(mask, min_distance):
    '''
    Crude method to find the approximate centers of the unconnected regions in a binary mask
    '''
    # smoothed distance transform
    dist = ndimage.distance_transform_edt(mask)
    distf = skimage.filters.gaussian(dist, sigma=1)

    # the positions of the local maximima in the distance transform
    # correspond roughly to the centers of mass of the individual nuclei
    positions = skimage.feature.peak_local_max(
        distf, indices=True, min_distance=min_distance, labels=mask
    )
    return positions


def generate_watershed_mask(mask, min_distance, background_mask=None):
    '''
    Watershed a binary mask using the distance transform approach
    mask : the binary mask to distance-transform
    min_distance : minimum distance between local maxima in the distance transform
        to use as seeds for the watershed
    background_mask : optional, less stringent mask to mask the watershed transform itself
    '''

    if background_mask is None:
        background_mask = mask

    dist = ndimage.distance_transform_edt(mask)
    distf = skimage.filters.gaussian(dist, sigma=1)

    local_max = skimage.feature.peak_local_max(
        distf, indices=False, min_distance=min_distance, labels=mask
    )
    labeled_local_max, num_local_max = ndimage.label(local_max)

    watershed_mask = skimage.morphology.watershed(
        -distf.astype(float),
        mask=background_mask,
        markers=labeled_local_max,
        watershed_line=True,
        compactness=.01
    )
    return watershed_mask
