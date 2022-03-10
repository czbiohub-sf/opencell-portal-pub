import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import { LocalizationAnnotation } from './localizationAnnotations.jsx';

import './popoverContents.css';


const VSpace = props => <div style={{'height': '15px', width: '100%'}}/>;

const commonProteinAbundanceNotes = (
    <>
    <p>
        These estimates are derived from the mass-spectrometric intensities
        using the approach described 
        in <a href='https://www.sciencedirect.com/science/article/pii/S1535947620337749' target='_blank'>
            Wisniewski et al., 2014
        </a>.
        Absolute values were obtained by normalizing with empirical estimates
        of 200pg for the total protein mass per cell and 1pL for the cellular volume
        of HEK293T cells. 
        Note that accuracy of these estimates is difficult to quantify for individual proteins,
        but is, on average, within a factor of two. 
    </p><p>
        To download these estimates for the entire HEK293T proteome, please visit 
        the "Protein abundance" section of the <Link to='/download'>data-download</Link> page.
    </p>
    </>
);

const proteinConcentration = (
    <div className='popover-container-wide'>
        <p>
            This is an estimate of the nanomolar intracellular protein concentration
            in HEK293T cells, derived from whole-cell mass spectrometry.
        </p>
        {commonProteinAbundanceNotes}
    </div>
);

const proteinCopyNumber = (
    <div className='popover-container-wide'>
        <p>
            This is an estimate of the number of copies of the protein per cell
            in HEK293T cells, derived from whole-cell mass spectrometry. 
        </p>
        {commonProteinAbundanceNotes}
    </div>
);
const imputedProteinAbundanceWarning = (
    <div className='popover-container-wide'>
        <p>
        <b>
            Warning: for this protein, estimates of protein concentration and copy number 
            as measured by whole-cell mass spectrometry are not available,
            so values imputed from RNA-Seq are shown here instead. 
        </b>
        <p></p>
        This usually means that this protein was detected in a protein group 
        that consists of more than one distinct protein, 
        preventing this protein from being assigned an unambiguous mass-spec intensity. 
        In rare cases, it may instead mean that no peptides corresponding to this protein 
        were detected during the mass-spec experiment.
        <p></p>
        In all such cases, estimates of protein concentration and copy number were obtained
        using linear regression to predict protein concentration 
        from the transcript abundance as measured by RNA-Seq.
        The regression model was trained on log-transformed data from all proteins 
        for which unambiguous measured values of both protein and transcript abundance were obtained.
    </p>
    </div>
);

const undetectedProteinAbundanceWarning = (
    <div className='popover-container-wide'>
        <p>
        <b>
            Expression of this protein was not detected in HEK293T cells
            using either RNAseq or whole-cell mass spectrometry. 
        </b>
        <p></p>
        Note that, for RNAseq, 'not detected' means that transcript expression
        was less than 1 transcript per million.
    </p>
    </div>
);

const searchResultsHeader = (
    <div className='popover-container-wide'>
    <p>
        Search for proteins in the human proteome by either gene name, protein name, or keyword.
    </p>
    <p>
        Please note that the search is performed over all protein-coding genes 
        in the <a href='https://www.genenames.org/' target='_blank'>HGNC database</a>.
        The search results do not include pseudogenes, alternative sequences, or protein isoforms. 
    </p>
    </div>
);

const searchResultsStatusColumn = (
    <div className='popover-container-wide'>
    <p>
        This column indicates how much information is available 
        from the OpenCell database for each protein.
    </p><p>
        <b>Targets</b> are proteins that have been tagged as part of the OpenCell project
        and for which both microscopy images and protein-protein interaction data is available.  
    </p><p>
        <b> Interactors</b> are proteins that have <b>not</b> yet been tagged
        but were observed to interact with one or more OpenCell targets by IP-MS. 
    </p><p>
        Proteins marked as <b>expressed</b> were observed to be expressed in HEK293T cells,
        but have not yet been tagged and also were not observed to interact with any OpenCell targets.
    </p><p>
        Finally, proteins marked as <b>not detected</b> were not found to be expressed in HEK293T cells. 
    </p>
</div>
);

const aboutThisProteinHeader = (
    <div className='popover-container-narrow'>
    <p>
    This is the functional annotation for the currently selected protein from UniprotKB.
    </p>
    </div>
);

const referenceDatabasesHeader = (
    <div className='popover-container-narrow'>
    <p>
    These are links to external reference databases for the currently selected protein.
    (HPA stands for the <a href='https://www.proteinatlas.org/about' target='_blank'>Human Protein Atlas</a>.)
    </p>
    </div>
);

const localizationHeader = (
    <div className='popover-container-wide'>
    <p>
        These are the subcellular localization annotations assigned by a human observer
        from the fluorescence microscopy images. Each category is assigned one of three 'grades,'
        which are represented by the colored rectangles as follows:
    </p>
    <VSpace/>
    <div className="w-100">
        <LocalizationAnnotation name='Prominent signal' grade='3'/>
        <LocalizationAnnotation name='Clearly detectable signal' grade='2'/>
        <LocalizationAnnotation name='Detectable but subtle and/or weak signal' grade='1'/>
    </div>
    </div>
);

const expressionLevelHeader = (
    <div className='popover-container-wide'>
        <p>
        This scatterplot compares two different estimates of protein expression on a base-10 log-log scale
        for all proteins expressed in HEK293T cells.
        </p><p>
        On the x-axis, relative transcript abundance from RNAseq data is plotted, in transcripts per million.
        On the y-axis, an estimate of absolute protein abundance from whole-cell mass spectrometry data is plotted,
        as a nanomolar cellular concentration.
        </p><p>
        The currently selected protein is highlighted in blue.
        </p>
    </div>
);

const cellLineTableHeader = (
    <div className='popover-container-wide'>
        <p>
        This table lists all 1,310 proteins that have been tagged as part of the OpenCell project.
        </p><p>
        Click on a column header to sort the table by the values in that column,
        and use the textbox below each column header to search within that column.
        </p>
    </div>
);

const microscopyHeader = (
    <div className='popover-container-wide'>
        <p>
            Tagged proteins are imaged in 3D in live cells using a spinning-disk
            confocal microscope with a 63x objective.
            There are three different ways of visualizing these 3D images:
        </p><p>
            The <b>2D projection mode</b> displays a maximum-intensity projection
            through the stack of confocal slices (along the z-axis).
            It provides a quick and compact overview of the full 3D image.
        </p><p>
            The <b>2D slice mode</b> displays a single confocal slice from the z-stack.
            Use the horizontal slider below the image viewer to scroll through the slices in the stack.
        </p><p>
            The <b>3D mode</b> displays the full 3D image as a volume rendering.
            This reveals the 3D structure in the image by displaying bright regions in the image
            as partially opaque 3D shapes (or volumes). 
            The degree of transparency is proportional to the intensity;
            black regions are completely transparent and correspond to areas of background in the image.
        </p>
    </div>
);

const microscopyChannel = (
    <div className='popover-container-narrow'>
    <p>
        Select the imaging channel to display.
    </p>
    <p>
        The <b>nucleus</b> channel shows the signal from the Hoechst stain used to label the DNA.
    </p><p>
        The <b>target</b> channel shows the signal from the split-mNeonGreen-tagged protein.
    </p><p>
        When the <b>'both channels'</b> option is selected,
        the nucleus channel (Hoechst staining) is overlaid in blue
        on top of the target channel (split-mNeonGreen signal), which is shown in gray.
    </p>
    </div>
);

const microscopyImageQuality = (
    <div className='popover-container-narrow'>
    <p>
        Select the quality of the 3D images.
    </p><p>
        When the quality is set to <b>auto</b>,
        the images are substantially compressed to ensure fast loading times.
        Compression artifacts will be visible in some images on this setting.
    </p><p>
        When the quality is set to <b>high</b>, the images are lightly compressed
        to preserve image quality, but at the expense of longer loading times.
    </p>
    </div>
);

const microscopyFovSelection = (
    <div className='popover-container-narrow'>
    <p>
        Select the image to view from among all available images of the selected protein.
        Each image represents a different position, or field of view (FOV), on the microscope.
    </p>
    </div>
);

const microscopyDownloadRaw = (
    <div className='popover-container-narrow'>
    <p>
        Click these buttons to download the raw image data for the currently selected image
        as a 16-bit TIFF file.
    </p><p>
        The <b>2D</b> button downloads a maximum-intensity z-projection. 
    </p><p>
        The <b>3D</b> button downloads the full raw confocal z-stack. 
        These files are between 100MB and 150MB in size, depending on the depth of the stack. 
    </p><p>
        Please see the <Link to='/download' target='_blank'>data page</Link> for more details about these files. 
    </p>
    </div>
);

const lowGfpWarning = (
    <div className='popover-container-narrow'>
        <p>
            The fluorescent signal from this tagged protein is low; 
            please interpret the images with caution.
        </p>
    </div>
);


const massSpecTargetPageHeader = (
    <div className='popover-container-wide'>
        <p>
            The proteins that interact with each OpenCell target are detected by IP-MS experiments,
            using the split-mNeonGreen tag as the affinity handle for the immunoprecipitation.
            This panel shows three different visualizations of the proteins that were observed 
            to interact with the currently selected OpenCell target:
        </p><p>
            The <b>interaction network</b> displays the network of all proteins that
            were observed to interact with the currently selected OpenCell target, 
            as well as the interactions between them.
        </p><p>
        </p><p>
            The <b>scatterplots</b> display quantitative information about each of the proteins
            that appeared in the pulldown of the currently selected OpenCell target.
        </p><p>
        </p><p>
            The <b>list of interactors</b> is a downloadable table of all of the interactors
            shown in the interaction network, along with their quantitative attributes
            (enrichment, interaction stiochiometry, etc).
        </p><p>
            Click on any protein name in either the interaction network or the list of interactors
            to jump to the page for that protein. 
        </p>
    </div>
);

const massSpecInteractorPageHeader = (
    <div className='popover-container-wide'>
        <p>
            The proteins that interact with each OpenCell target are detected by IP-MS experiments,
            using the split-mNeonGreen tag as the affinity handle for the immunoprecipitation.
            Although the currently selected protein is not an OpenCell target, 
            it was observed to interact with one or more OpenCell targets 
            (that is, it appeared as a statistically significant hit in one or more OpenCell pulldowns).
            These OpenCell targets constitute a subset of the interactome 
            of the currently selected protein. They are visualized below in two ways:
        </p><p>
            The <b>interaction network</b> displays the network of all OpenCell targets
            in whose pulldowns the currently selected protein appeared as an interactor,
            as well as the interactions between them. 
        </p><p>
        </p><p>
            The <b>list of interactors</b> is a downloadable table of all of the interactors
            shown in the interaction network, along with their quantitative attributes
            (enrichment, interaction stiochiometry, etc).
        </p><p>
            Click on any protein name in either the interaction network or the list of interactors
            to jump to the page for that protein. 
        </p>

    </div>
);

const interactionNetworkHeader = (
    <div className='popover-container-wide'>
    <p>
        This displays an interactive network representation of the protein-protein interactions
        for the currently selected protein.
    </p><p>
        Proteins are represented by <b>nodes</b> and significant interactions
        between them are represented by <b>edges</b> between nodes (the light gray lines).
        You can navigate to the page for any protein by clicking on its node.
        The currently selected protein is highlighted in blue, 
        and interactors shown in <b>bold</b> are themselves OpenCell targets.
    </p><p>
        We use <a href='https://mcans.org/mcl/' target='_blank'> a type of unsupervised clustering</a> of
        the whole interactome to group highly connected proteins
        into <b>functional modules</b>. These are represented by the lightly shaded gray boxes.
        Within these modules, <b>core complexes</b> are represented by the slightly darker shaded boxes.
        These core complex clusters are defined using high-stoichiometry interactions
        (see the stoichiometry plots under the 'Scatterplots' tab for more details).
    </p><p>
        Please note that large interactomes are hard to compactly arrange in two dimensions.
        Try clicking the <b>'Re-run layout'</b> button to generate a different layout.
    </p>
    </div>
);

const scatterplotsHeader = (
    <div className='popover-container-wide'>
    <p>
    This displays scatterplots of quantitative information 
    about each protein-protein interaction (PPI) for the currently selected OpenCell target.
    Each dot represents a protein (or group of homologs) that interacts with the currently selected target.
    Each plot is interactive (use <b>'Show labels'</b> to toggle dot labels on/off
    and <b>Reset zoom</b> after panning or zooming).
    </p><p>
    <b>The volcano plot mode</b> represents a statistical definition of PPIs in pull-downs
    of the selected target.
    Each dot represents the relative enrichment of the interacting protein (on the x-axis)
    and its associated p-value (on the y-axis).
    The enrichment value of each interactor is calculated relative to its enrichment
    in hundreds of other OpenCell pulldowns,
    and p-values are calculated from a t-test using triplicate observations of each interactor.
    We defined statistically significant interactions using two thresholds for false discovery rate:
    a very stringent 'major hit' threshold, and a more relaxed 'minor hit' threshold.
    </p><p>
    <b>The stoichiometry plot mode</b> represents stoichiometry information of PPIs
    as defined <a href='https://www.cell.com/cell/fulltext/S0092-8674(15)01270-2' target='_blank'>here</a>.
    The <b>interaction stoichiometry</b> (on the x-axis) corresponds to the abundance ratio
    of an interactor to that of the target protein in triplicate pull-downs.
    The <b>cellular abundance stoichiometry</b> (on the y-axis) corresponds to the abundance ratio from expression
    in the whole cell. The shaded circle in the plot is the 'core-complex zone,'
    determined empirically to be enriched for stable protein interactions.
    </p><p>
    Please note that, for some targets, <b>no data</b> is displayed in this tab. This occurs for targets
    that do not have their own IP-MS (immunoprecipitation-mass spectrometry) dataset yet.
    For these targets, the interaction network is derived from the IP-MS data for all other OpenCell targets.
    </p><p>
    Additionally, because the interaction stoichiometry values are normalized to the target,
    if the target was not detected in its own pull-down,
    the stoichiometry calculations are impossible and no data can be displayed in the stoichiometry scatterplot.
    </p>
    </div>
);

const interactionTableHeader = (
    <div className='popover-container-wide'>
    <p>
    This displays a table that lists all of the proteins that were observed to interact with the currently selected protein.
    For each interaction, the <b>bait</b> column corresponds to the name of the tagged protein
    that was pulled down and the <b>prey</b> column corresponds to the interacting protein
    that was detected in that pull-down.
    Note that an OpenCell target can appear either as a bait or a prey (or both) in this list.
    </p><p>
    The quantitative columns include the <b>p-value</b> (-log10) and the <b>relative enrichment </b>
    from the volcano plot, as well as the <b>cellular abundance stoichiometry</b>
    and the <b>interaction stoichiometry</b> (both in log10) from the stoichiometry plot.
    (for more details, refer to the scatterplot tab).
    </p><p>
    When both interactors belong to the same functional module (the shaded boxes in 'Network' tab),
    the module ID is specified as the 'Cluster ID'. These IDs are unique but not human-readable;
    we are working on appending meaningful biological annotations to these clusters.
    </p><p>
    Below the table, the <b>'Export table as CSV'</b> button allows you to download
    the whole interactors table for the currently selected target as a CSV file.
    </p>
    </div>
);


const sequencingHeader = (
    <div className='popover-container-wide'>
    <p>
        This bar chart summarizes the results of amplicon sequencing 
        to characterize the frequency of edited and wild-type alleles 
        in each tagged cell line. 
        </p><p>
        The <b>HDR</b> (homology-directed repair) category corresponds to 'perfect' (error-less) insertions
        of the split-mNeonGreen sequence.
        These alleles are expected to be functional and are the source 
        of the fluorescent signal in the microscopy images.
        </p><p>
        The <b>other</b> category corresponds to other repair outcomes that are the product
        of non-homologous end-joining (NHEJ), which competes with HDR for the repair of double-strand breaks.
        These repair outcomes are predominately non-functional and therefore do not complicate
        the interpretation of the fluorescence microscopy or mass-spec data.
        </p><p>
        The <b>WT</b> (wild-type) category corresponds to unedited (and therefore non-fluorescent) alleles.
    </p>
    </div>
);

const galleryHeader = (
    <div className='popover-container-wide'>
    <p>
        This page displays the microscopy images for all tagged proteins in the OpenCell library,
        filtered by the selected subcellular localization categories.
        Each tagged protein is represented by a thumbnail microscopy image
        in which the fluorescently tagged protein is shown in gray
        and the nuclear staining is overlaid in blue.
    </p><p>
        Click on a thumbnail to view the full-size microscopy images,
        and click on a protein name to open the page for that protein in a new window.
    </p>
    </div>
);

const gallerySelectionMode = (
    <div className='popover-container-narrow'>
    <p>
        Choose <b>all</b> to view only proteins assigned to <b>all</b> of the selected categories.
    </p><p>
        Choose <b>any</b> to view proteins assigned to any one (or more) of the selected categories.
    </p><p>
        Hint: the <b>all</b> option is useful to view multi-localizing proteins, 
        while the <b>any</b> option is useful to juxtapose proteins with unrelated localization categories.
    </p>
    </div>
);


// unwritten popovers
const umapGridSize = null;
const umapMarkerType = null;
const umapSnapToGrid = null;


// template
const _ = (
    <div className='popover-container-narrow'>
    <p>
    </p>
    </div>
);


export {
    proteinConcentration,
    proteinCopyNumber,
    imputedProteinAbundanceWarning,
    undetectedProteinAbundanceWarning,

    searchResultsHeader,
    searchResultsStatusColumn,
    aboutThisProteinHeader,
    referenceDatabasesHeader,
    sequencingHeader,
    localizationHeader,
    expressionLevelHeader,
    cellLineTableHeader,

    microscopyHeader,
    microscopyChannel,
    microscopyFovSelection,
    microscopyImageQuality,
    microscopyDownloadRaw,
    lowGfpWarning,

    massSpecTargetPageHeader,
    massSpecInteractorPageHeader,
    interactionNetworkHeader,
    scatterplotsHeader,
    interactionTableHeader,

    galleryHeader,
    gallerySelectionMode,

    umapGridSize,
    umapSnapToGrid,
    umapMarkerType,
}
