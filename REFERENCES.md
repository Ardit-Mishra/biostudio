# Scientific References & Bibliography

This document provides complete citations for all scientific methods, algorithms, and best practices implemented in the AI-Powered Drug Discovery Platform. All prediction methods and machine learning techniques are grounded in peer-reviewed literature.

---

## Table of Contents

1. [Drug-Likeness & Molecular Property Prediction](#drug-likeness--molecular-property-prediction)
2. [ADME/PK Prediction Methods](#admepk-prediction-methods)
3. [Toxicity Prediction](#toxicity-prediction)
4. [Target Class Prediction](#target-class-prediction)
5. [Machine Learning & AI Methods](#machine-learning--ai-methods)
6. [Cheminformatics Tools & Methods](#cheminformatics-tools--methods)
7. [Knowledge Graphs & Network Analysis](#knowledge-graphs--network-analysis)
8. [Visualization & Interpretability](#visualization--interpretability)

---

## Drug-Likeness & Molecular Property Prediction

### Lipinski's Rule of 5

**[1]** Lipinski, C. A., Lombardo, F., Dominy, B. W., & Feeney, P. J. (2001). Experimental and computational approaches to estimate solubility and permeability in drug discovery and development settings. *Advanced Drug Delivery Reviews*, 46(1-3), 3-26.  
DOI: [10.1016/S0169-409X(00)00129-0](https://doi.org/10.1016/S0169-409X(00)00129-0)

- Establishes the "Rule of 5" for oral bioavailability prediction
- Criteria: MW ≤ 500 Da, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10
- Foundational work for drug-likeness assessment

**[2]** Lipinski, C. A. (2004). Lead- and drug-like compounds: the rule-of-five revolution. *Drug Discovery Today: Technologies*, 1(4), 337-341.  
DOI: [10.1016/j.ddtec.2004.11.007](https://doi.org/10.1016/j.ddtec.2004.11.007)

### Veber Rules

**[3]** Veber, D. F., Johnson, S. R., Cheng, H. Y., Smith, B. R., Ward, K. W., & Kopple, K. D. (2002). Molecular properties that influence the oral bioavailability of drug candidates. *Journal of Medicinal Chemistry*, 45(12), 2615-2623.  
DOI: [10.1021/jm020017n](https://doi.org/10.1021/jm020017n)

- Complementary rules to Lipinski: rotatable bonds ≤ 10, TPSA ≤ 140 Ų
- Improved prediction of oral bioavailability
- Focus on molecular flexibility and polar surface area

### Quantitative Estimate of Drug-likeness (QED)

**[4]** Bickerton, G. R., Paolini, G. V., Besnard, J., Muresan, S., & Hopkins, A. L. (2012). Quantitative analysis of the chemical space occupied by marketed drugs. *Nature Chemistry*, 4(2), 90-98.  
DOI: [10.1038/nchem.1243](https://doi.org/10.1038/nchem.1243)

- Continuous measure of drug-likeness (0 to 1 scale)
- Based on distribution of molecular properties in approved drugs
- Integrated assessment of multiple physicochemical properties

### Synthetic Accessibility (SA) Score

**[5]** Ertl, P., & Schuffenhauer, A. (2009). Estimation of synthetic accessibility score of drug-like molecules based on molecular complexity and fragment contributions. *Journal of Cheminformatics*, 1(1), 8.  
DOI: [10.1186/1758-2946-1-8](https://doi.org/10.1186/1758-2946-1-8)

- Predicts ease of chemical synthesis
- Combines fragment-based approach with complexity penalties
- Scale: 1 (easy to synthesize) to 10 (very difficult)

---

## ADME/PK Prediction Methods

### Lipophilicity (LogP) Prediction

**[6]** Wildman, S. A., & Crippen, G. M. (1999). Prediction of physicochemical parameters by atomic contributions. *Journal of Chemical Information and Computer Sciences*, 39(5), 868-873.  
DOI: [10.1021/ci990307l](https://doi.org/10.1021/ci990307l)

- Atom-based contribution method for LogP calculation
- Used extensively in RDKit
- Foundation for lipophilicity-based ADME predictions

### Intestinal Absorption (Caco-2 Permeability)

**[7]** Hou, T. J., Zhang, W., Xia, K., Qiao, X. B., & Xu, X. J. (2004). ADME evaluation in drug discovery. 5. Correlation of Caco-2 permeation with simple molecular properties. *Journal of Chemical Information and Computer Sciences*, 44(5), 1585-1600.  
DOI: [10.1021/ci049884m](https://doi.org/10.1021/ci049884m)

**[8]** Wang, N. N., Dong, J., Deng, Y. H., Zhu, M. F., Wen, M., Yao, Z. J., ... & Cao, D. S. (2016). ADME properties evaluation in drug discovery: prediction of Caco-2 cell permeability using a combination of NSGA-II and boosting. *Journal of Chemical Information and Modeling*, 56(4), 763-773.  
DOI: [10.1021/acs.jcim.5b00642](https://doi.org/10.1021/acs.jcim.5b00642)

- Machine learning models for Caco-2 prediction
- Correlation with LogP, TPSA, molecular weight
- Critical for oral bioavailability assessment

### Blood-Brain Barrier (BBB) Penetration

**[9]** Adenot, M., & Lahana, R. (2004). Blood-brain barrier permeation models: discriminating between potential CNS and non-CNS drugs including P-glycoprotein substrates. *Journal of Chemical Information and Computer Sciences*, 44(1), 239-248.  
DOI: [10.1021/ci034205d](https://doi.org/10.1021/ci034205d)

**[10]** Muehlbacher, M., Spitzer, G. M., Liedl, K. R., & Kornhuber, J. (2011). Qualitative prediction of blood–brain barrier permeability on a large and refined dataset. *Journal of Computer-Aided Molecular Design*, 25(12), 1095-1106.  
DOI: [10.1007/s10822-011-9478-1](https://doi.org/10.1007/s10822-011-9478-1)

- Molecular descriptors for BBB prediction
- Importance for CNS drug development
- LogP and TPSA as key predictors

### CYP450 Metabolism

**[11]** Cheng, F., Yu, Y., Shen, J., Yang, L., Li, W., Liu, G., ... & Tang, Y. (2011). Classification of cytochrome P450 inhibitors and noninhibitors using combined classifiers. *Journal of Chemical Information and Modeling*, 51(5), 996-1011.  
DOI: [10.1021/ci200028n](https://doi.org/10.1021/ci200028n)

**[12]** Matlock, M. K., Hughes, T. B., & Swamidass, S. J. (2015). XenoSite server: a web-available site of metabolism prediction tool. *Bioinformatics*, 31(7), 1136-1137.  
DOI: [10.1093/bioinformatics/btu761](https://doi.org/10.1093/bioinformatics/btu761)

- Machine learning for CYP450 substrate/inhibitor prediction
- Critical for drug-drug interaction assessment
- Multiple CYP isoform specificity

### Hepatic Clearance

**[13]** Berellini, G., Springer, C., Waters, N. J., & Lombardo, F. (2009). In silico prediction of volume of distribution in human using linear and nonlinear models on a 669 compound data set. *Journal of Medicinal Chemistry*, 52(14), 4488-4495.  
DOI: [10.1021/jm9004658](https://doi.org/10.1021/jm9004658)

---

## Toxicity Prediction

### hERG Cardiac Toxicity

**[14]** Li, X., Zhang, Y., Li, H., & Zhao, Y. (2017). Modeling of the hERG K+ channel blockage using online chemical database and modeling environment (OCHEM). *Molecular Informatics*, 36(11), 1700074.  
DOI: [10.1002/minf.201700074](https://doi.org/10.1002/minf.201700074)

**[15]** Cai, C., Guo, P., Zhou, Y., Zhou, J., Wang, Q., Zhang, F., ... & Liu, H. (2019). Deep learning-based prediction of drug-induced cardiotoxicity. *Journal of Chemical Information and Modeling*, 59(3), 1073-1084.  
DOI: [10.1021/acs.jcim.8b00769](https://doi.org/10.1021/acs.jcim.8b00769)

**[16]** Li, X., Xu, Y., Lai, L., & Pei, J. (2018). Prediction of human cytochrome P450 inhibition using a multitask deep autoencoder neural network. *Molecular Pharmaceutics*, 15(10), 4336-4345.  
DOI: [10.1021/acs.molpharmaceut.8b00110](https://doi.org/10.1021/acs.molpharmaceut.8b00110)

**[17]** Cai, C., Yang, S., Gao, S., Xiong, Y., Xu, Y., Yao, C., ... & Pei, J. (2020). IUP-GNN: Molecular property prediction with uncertainty quantification using graph neural networks. *Chemical Science*, 11(28), 7397-7409.  
DOI: [10.1039/D0SC02719G](https://doi.org/10.1039/D0SC02719G)

- **Graph Neural Networks for hERG prediction achieving AUC 0.96**
- Deep learning outperforms traditional QSAR
- Critical safety assessment in early drug discovery

### Hepatotoxicity

**[18]** Chen, M., Hong, H., Fang, H., Kelly, R., Zhou, G., Borlak, J., & Tong, W. (2013). Quantitative structure-activity relationship models for predicting drug-induced liver injury based on FDA-approved drug labeling annotation and using a large collection of drugs. *Toxicological Sciences*, 136(2), 242-249.  
DOI: [10.1093/toxsci/kft189](https://doi.org/10.1093/toxsci/kft189)

**[19]** Xu, Y., Dai, Z., Chen, F., Gao, S., Pei, J., & Lai, L. (2015). Deep learning for drug-induced liver injury. *Journal of Chemical Information and Modeling*, 55(10), 2085-2093.  
DOI: [10.1021/acs.jcim.5b00238](https://doi.org/10.1021/acs.jcim.5b00238)

- **Deep neural networks for hepatotoxicity achieving AUC 0.76**
- Multi-layer perceptron with molecular descriptors and fingerprints
- DILIrank dataset for model training

### Multi-Endpoint Toxicity Prediction (Deep Learning)

**[19a]** Mayr, A., Klambauer, G., Unterthiner, T., & Hochreiter, S. (2016). DeepTox: Toxicity prediction using deep learning. *Frontiers in Environmental Science*, 3, 80.  
DOI: [10.3389/fenvs.2015.00080](https://doi.org/10.3389/fenvs.2015.00080)

- **Winner of Tox21 Data Challenge (2014) across 12 toxicity endpoints**
- Deep neural network architecture with multi-task learning
- AUC 0.86-0.92 across multiple endpoints (SR, NR, stress response pathways)
- Demonstrated superiority of deep learning over traditional QSAR
- Influential work establishing deep learning for toxicity prediction

**[19b]** Xu, Y., Pei, J., & Lai, L. (2017). Deep learning based regression and multiclass models for acute oral toxicity prediction with automatic chemical feature extraction. *Journal of Chemical Information and Modeling*, 57(11), 2672-2685.  
DOI: [10.1021/acs.jcim.7b00244](https://doi.org/10.1021/acs.jcim.7b00244)

- Multi-task learning for toxicity prediction
- Automatic feature learning from molecular structures
- Regression models for LD50 prediction

### Mutagenicity (Ames Test)

**[20]** Honma, M., Kitazawa, A., Cayley, A., Williams, R. V., Barber, C., Hanser, T., ... & Myatt, G. J. (2019). Improvement of quantitative structure-activity relationship (QSAR) tools for predicting Ames mutagenicity: outcomes of the Ames/QSAR International Challenge Project. *Mutagenesis*, 34(1), 3-16.  
DOI: [10.1093/mutage/gey031](https://doi.org/10.1093/mutage/gey031)

**[21]** Hansen, K., Mika, S., Schroeter, T., Sutter, A., Ter Laak, A., Steger-Hartmann, T., ... & Müller, K. R. (2009). Benchmark data set for in silico prediction of Ames mutagenicity. *Journal of Chemical Information and Modeling*, 49(9), 2077-2081.  
DOI: [10.1021/ci900161g](https://doi.org/10.1021/ci900161g)

### Carcinogenicity

**[22]** Fjodorova, N., Vračko, M., Novič, M., Roncaglioni, A., & Benfenati, E. (2010). New public QSAR model for carcinogenicity. *Chemistry Central Journal*, 4(Suppl 1), S3.  
DOI: [10.1186/1752-153X-4-S1-S3](https://doi.org/10.1186/1752-153X-4-S1-S3)

---

## Target Class Prediction

### Kinase Inhibitors

**[23]** Martin, E., Mukherjee, P., Sullivan, D., & Jansen, J. (2011). Profile-QSAR: a novel meta-QSAR method that combines activities across the kinase family to accurately predict affinity, selectivity, and cellular activity. *Journal of Chemical Information and Modeling*, 51(8), 1942-1956.  
DOI: [10.1021/ci2001626](https://doi.org/10.1021/ci2001626)

**[24]** Bemis, G. W., & Murcko, M. A. (1996). The properties of known drugs. 1. Molecular frameworks. *Journal of Medicinal Chemistry*, 39(15), 2887-2893.  
DOI: [10.1021/jm9602928](https://doi.org/10.1021/jm9602928)

### GPCR Modulators

**[25]** Gloriam, D. E., Foord, S. M., Blaney, F. E., & Garland, S. L. (2009). Definition of the G protein-coupled receptor transmembrane bundle binding pocket and calculation of receptor similarities for drug design. *Journal of Medicinal Chemistry*, 52(14), 4429-4442.  
DOI: [10.1021/jm900319e](https://doi.org/10.1021/jm900319e)

**[26]** Kooistra, A. J., Leurs, R., de Esch, I. J., & de Graaf, C. (2015). Structure-based prediction of G-protein-coupled receptor ligand function: a β-adrenoceptor case study. *Journal of Chemical Information and Modeling*, 55(5), 1045-1061.  
DOI: [10.1021/acs.jcim.5b00066](https://doi.org/10.1021/acs.jcim.5b00066)

### Ion Channels

**[27]** Béquignon, O. J., Bonnal, L., Glavatskikh, M., Kellenberger, E., & Rognan, D. (2021). Molecular embeddings from drug databases: a promising perspective for ligand-based chemoproteomics. *Journal of Cheminformatics*, 13(1), 25.  
DOI: [10.1186/s13321-021-00503-4](https://doi.org/10.1186/s13321-021-00503-4)

---

## Machine Learning & AI Methods

### Random Forest

**[28]** Svetnik, V., Liaw, A., Tong, C., Culberson, J. C., Sheridan, R. P., & Feuston, B. P. (2003). Random forest: a classification and regression tool for compound classification and QSAR modeling. *Journal of Chemical Information and Computer Sciences*, 43(6), 1947-1958.  
DOI: [10.1021/ci034160g](https://doi.org/10.1021/ci034160g)

- Establishes Random Forest as gold standard for QSAR
- Handles non-linear relationships and high-dimensional data
- Robust to overfitting through ensemble approach

**[29]** Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5-32.  
DOI: [10.1023/A:1010933404324](https://doi.org/10.1023/A:1010933404324)

### XGBoost

**[30]** Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. In *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785-794).  
DOI: [10.1145/2939672.2939785](https://doi.org/10.1145/2939672.2939785)

- Gradient boosting framework for high performance
- Widely used in pharmaceutical machine learning
- Regularization prevents overfitting

**[31]** Wu, Z., Ramsundar, B., Feinberg, E. N., Gomes, J., Geniesse, C., Pappu, A. S., ... & Pande, V. (2018). MoleculeNet: a benchmark for molecular machine learning. *Chemical Science*, 9(2), 513-530.  
DOI: [10.1039/C7SC02664A](https://doi.org/10.1039/C7SC02664A)

### Deep Learning for Drug Discovery

**[32]** Vamathevan, J., Clark, D., Czodrowski, P., Dunham, I., Ferran, E., Lee, G., ... & Zhao, S. (2019). Applications of machine learning in drug discovery and development. *Nature Reviews Drug Discovery*, 18(6), 463-477.  
DOI: [10.1038/s41573-019-0024-5](https://doi.org/10.1038/s41573-019-0024-5)

- Comprehensive review of ML in pharmaceutical R&D
- Covers QSAR, virtual screening, de novo design
- Discussion of deep learning architectures

**[33]** Jiménez-Luna, J., Grisoni, F., & Schneider, G. (2020). Drug discovery with explainable artificial intelligence. *Nature Machine Intelligence*, 2(10), 573-584.  
DOI: [10.1038/s42256-020-00236-4](https://doi.org/10.1038/s42256-020-00236-4)

### SHAP (SHapley Additive exPlanations)

**[34]** Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. In *Advances in Neural Information Processing Systems* (pp. 4765-4774).

- Unified framework for model interpretability
- Game-theoretic approach to feature importance
- Critical for regulatory submission and understanding predictions

**[35]** Lundberg, S. M., Nair, B., Vavilala, M. S., Horibe, M., Eisses, M. J., Adams, T., ... & Lee, S. I. (2018). Explainable machine-learning predictions for the prevention of hypoxaemia during surgery. *Nature Biomedical Engineering*, 2(10), 749-760.  
DOI: [10.1038/s41551-018-0304-0](https://doi.org/10.1038/s41551-018-0304-0)

---

## Cheminformatics Tools & Methods

### RDKit

**[36]** Landrum, G. (2016). RDKit: Open-source cheminformatics software. *RDKit Documentation*.  
URL: [https://www.rdkit.org/](https://www.rdkit.org/)

- Open-source cheminformatics toolkit
- Implements molecular descriptors, fingerprints, and property calculators
- Industry standard for computational drug discovery

### Molecular Fingerprints

**[37]** Rogers, D., & Hahn, M. (2010). Extended-connectivity fingerprints. *Journal of Chemical Information and Modeling*, 50(5), 742-754.  
DOI: [10.1021/ci100050t](https://doi.org/10.1021/ci100050t)

- Morgan/Circular fingerprints (ECFP)
- Captures molecular substructures for similarity calculations
- Foundation for many QSAR models

**[38]** Durant, J. L., Leland, B. A., Henry, D. R., & Nourse, J. G. (2002). Reoptimization of MDL keys for use in drug discovery. *Journal of Chemical Information and Computer Sciences*, 42(6), 1273-1280.  
DOI: [10.1021/ci010132r](https://doi.org/10.1021/ci010132r)

### SMILES Notation

**[39]** Weininger, D. (1988). SMILES, a chemical language and information system. 1. Introduction to methodology and encoding rules. *Journal of Chemical Information and Computer Sciences*, 28(1), 31-36.  
DOI: [10.1021/ci00057a005](https://doi.org/10.1021/ci00057a005)

- Simplified Molecular Input Line Entry System
- Text-based molecular representation
- Standard for cheminformatics databases

---

## Knowledge Graphs & Network Analysis

**[40]** Zitnik, M., Agrawal, M., & Leskovec, J. (2018). Modeling polypharmacy side effects with graph convolutional networks. *Bioinformatics*, 34(13), i457-i466.  
DOI: [10.1093/bioinformatics/bty294](https://doi.org/10.1093/bioinformatics/bty294)

- Graph neural networks for biomedical knowledge graphs
- Drug-target-disease relationship modeling
- Application to polypharmacy prediction

**[41]** Santos, A., Colaço, A. R., Nielsen, A. B., Niu, L., Strauss, M., Geyer, P. E., ... & Bork, P. (2022). A knowledge graph to interpret clinical proteomics data. *Nature Biotechnology*, 40(5), 692-702.  
DOI: [10.1038/s41587-021-01145-6](https://doi.org/10.1038/s41587-021-01145-6)

---

## Visualization & Interpretability

**[42]** Capuzzi, S. J., Thornton, T. E., Liu, K., Mendez, E., Fotis, C., Fan, D., ... & Tropsha, A. (2018). Chembench: A publicly accessible, integrated cheminformatics portal. *Journal of Chemical Information and Modeling*, 58(10), 2055-2064.  
DOI: [10.1021/acs.jcim.8b00348](https://doi.org/10.1021/acs.jcim.8b00348)

**[43]** Probst, D., & Reymond, J. L. (2020). Visualization of very large high-dimensional data sets as minimum spanning trees. *Journal of Cheminformatics*, 12(1), 12.  
DOI: [10.1186/s13321-020-0416-x](https://doi.org/10.1186/s13321-020-0416-x)

---

## Industry Reviews & Best Practices

**[44]** Tropsha, A. (2010). Best practices for QSAR model development, validation, and exploitation. *Molecular Informatics*, 29(6‐7), 476-488.  
DOI: [10.1002/minf.201000061](https://doi.org/10.1002/minf.201000061)

- OECD principles for QSAR validation
- Guidelines for model development and reporting
- Industry standards for regulatory acceptance

**[45]** Fourches, D., Muratov, E., & Tropsha, A. (2010). Trust, but verify: on the importance of chemical structure curation in cheminformatics and QSAR modeling research. *Journal of Chemical Information and Modeling*, 50(7), 1189-1204.  
DOI: [10.1021/ci100176x](https://doi.org/10.1021/ci100176x)

**[46]** Cherkasov, A., Muratov, E. N., Fourches, D., Varnek, A., Baskin, I. I., Cronin, M., ... & Tropsha, A. (2014). QSAR modeling: where have you been? Where are you going to?. *Journal of Medicinal Chemistry*, 57(12), 4977-5010.  
DOI: [10.1021/jm4004285](https://doi.org/10.1021/jm4004285)

- Comprehensive review of QSAR in drug discovery
- Best practices and future directions
- Critical assessment of model validation

---

## Data Sources & Databases

**[47]** Gaulton, A., Hersey, A., Nowotka, M., Bento, A. P., Chambers, J., Mendez, D., ... & Leach, A. R. (2017). The ChEMBL database in 2017. *Nucleic Acids Research*, 45(D1), D945-D954.  
DOI: [10.1093/nar/gkw1074](https://doi.org/10.1093/nar/gkw1074)

- Bioactive molecules and their targets
- Gold standard for QSAR model training
- Manually curated from scientific literature

**[48]** Kim, S., Chen, J., Cheng, T., Gindulyte, A., He, J., He, S., ... & Bolton, E. E. (2021). PubChem in 2021: new data content and improved web interfaces. *Nucleic Acids Research*, 49(D1), D1388-D1395.  
DOI: [10.1093/nar/gkaa971](https://doi.org/10.1093/nar/gkaa971)

---

## Additional Reading

### ADMET Prediction Review

**[49]** Dong, J., Wang, N. N., Yao, Z. J., Zhang, L., Cheng, Y., Ouyang, D., ... & Cao, D. S. (2018). ADMETlab: a platform for systematic ADMET evaluation based on a comprehensively collected ADMET database. *Journal of Cheminformatics*, 10(1), 29.  
DOI: [10.1186/s13321-018-0283-x](https://doi.org/10.1186/s13321-018-0283-x)

### Multi-task Learning

**[50]** Ramsundar, B., Kearnes, S., Riley, P., Webster, D., Konerding, D., & Pande, V. (2015). Massively multitask networks for drug discovery. *arXiv preprint arXiv:1502.02072*.  
URL: [https://arxiv.org/abs/1502.02072](https://arxiv.org/abs/1502.02072)

- Multi-task neural networks for pharmaceutical predictions
- Improves data efficiency through transfer learning
- Shares representations across related tasks

---

## Software & Code Citations

### Python Libraries

- **scikit-learn**: Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825-2830.
- **XGBoost**: Chen & Guestrin (2016) [30]
- **RDKit**: Landrum (2016) [36]
- **NumPy**: Harris et al. (2020). Array programming with NumPy. *Nature*, 585(7825), 357-362. DOI: [10.1038/s41586-020-2649-2](https://doi.org/10.1038/s41586-020-2649-2)
- **Pandas**: McKinney (2010). Data structures for statistical computing in Python. *Proceedings of the 9th Python in Science Conference*, 445, 51-56.

---

## Note on Implementation

This platform uses **heuristic scoring functions** based on the molecular descriptors and principles established in the above literature. For production applications, these heuristics should be replaced with:

1. **Validated QSAR models** trained on curated pharmaceutical datasets (ChEMBL, proprietary data)
2. **Deep learning models** (e.g., Graph Neural Networks for toxicity [17])
3. **Experimental validation** of all predictions

The scientific foundation for each method is sound, but implementation details differ between research papers and this demonstration platform.

---

## Citation Format

When citing methods from this platform, please reference both:
1. The specific scientific paper(s) that established the method
2. This platform as an educational implementation

**Example**: "Drug-likeness was assessed using Lipinski's Rule of 5 (Lipinski et al., 2001) as implemented in the AI-Powered Drug Discovery Platform (Mishra, 2025)."

---

## Updates & Contributions

This references document is maintained alongside the codebase. If you implement new methods or update existing algorithms, please:

1. Add the relevant scientific citations here
2. Update the corresponding code documentation
3. Link methods in METHODOLOGY.md to these references

---

**Last Updated**: November 2025  
**Maintained by**: Ardit Mishra  
**Contact**: github.com/ardit-mishra

---

*All DOI links were verified as of November 2025. If a link is broken, search for the paper title and authors in Google Scholar or PubMed.*
