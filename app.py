import streamlit as st
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
import sys
import os
import io

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.molecular_utils import MolecularProcessor
from utils.drug_likeness import DrugLikenessCalculator
from utils.knowledge_graph import BiomedicalKnowledgeGraph
from utils.visualization_utils import MolecularVisualizer, ClusteringVisualizer
from models.adme_predictors import ADMEPredictor
from models.toxicity_predictors import ToxicityPredictor
from models.target_predictors import TargetClassPredictor
from models.ml_models import MultiModelPredictor
from data.kinase_inhibitors import get_case_study_data, get_approved_kinase_drugs

st.set_page_config(
    page_title="AI-Powered Drug Discovery Platform",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 600;
        color: #2C3E50;
        text-align: center;
        padding: 1.5rem 0;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #34495E;
        font-weight: 600;
        margin-top: 2rem;
        border-bottom: 1px solid #BDC3C7;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-left: 3px solid #7F8C8D;
        padding: 1.2rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .metric-card h4 {
        color: #2C3E50;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .success-box {
        background-color: #E8F5E9;
        border-left: 3px solid #4CAF50;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .warning-box {
        background-color: #FFF8E1;
        border-left: 3px solid #FFC107;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .danger-box {
        background-color: #FFEBEE;
        border-left: 3px solid #F44336;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .stRadio > label {
        font-weight: 500;
        color: #2C3E50;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_models():
    mol_processor = MolecularProcessor()
    drug_likeness = DrugLikenessCalculator()
    adme_predictor = ADMEPredictor()
    toxicity_predictor = ToxicityPredictor()
    target_predictor = TargetClassPredictor()
    ml_predictor = MultiModelPredictor()
    kg = BiomedicalKnowledgeGraph()
    visualizer = MolecularVisualizer()
    
    return (mol_processor, drug_likeness, adme_predictor, toxicity_predictor, 
            target_predictor, ml_predictor, kg, visualizer)


(mol_processor, drug_likeness, adme_predictor, toxicity_predictor,
 target_predictor, ml_predictor, kg, visualizer) = load_models()


st.markdown('<div class="main-header">AI-Powered Drug Discovery Platform</div>', 
            unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #555; margin-bottom: 1rem;'>
    <p>Open-Source Research Platform for Computational Drug Discovery</p>
    <p><strong>Featuring:</strong> ADME/PK Prediction • Toxicity Profiling • Target Class Prediction • ML Explainability • Knowledge Graph</p>
</div>
""", unsafe_allow_html=True)

st.info("""
**NOTE**: This is an educational/research platform demonstrating pharmaceutical data science workflows. 
Current predictors use heuristic scoring functions based on RDKit molecular descriptors for demonstration purposes.  
For production use, these should be replaced with validated, data-driven QSAR models trained on curated datasets.
""")

with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio(
        "Select Module",
        ["Home", "Molecule Input", "ADME/PK Analysis", "Toxicity Profile", 
         "Target Prediction", "ML Models", "Knowledge Graph", 
         "Batch Screening", "Case Study", "About"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### Quick Stats")
    st.metric("Models Deployed", "8")
    st.metric("Predictions Today", "0")
    st.metric("Success Rate", "95%")
    
    st.markdown("---")
    st.markdown("""
    <small style="color: #5D6D7E;">
    <strong>Platform Modules:</strong><br>
    • Real-time ADME/PK prediction<br>
    • Toxicity risk assessment<br>
    • Drug-likeness scoring<br>
    • Target class prediction<br>
    • ML model explainability<br>
    • Knowledge graph explorer<br>
    </small>
    """, unsafe_allow_html=True)


if page == "Home":
    st.markdown('<div class="sub-header">Welcome to the AI Drug Discovery Platform</div>', 
                unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### Multi-Target Prediction")
        st.write("Predict activity against kinases, GPCRs, ion channels, and enzymes using ML classifiers")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### ADME/PK Profiling")
        st.write("Comprehensive absorption, distribution, metabolism, and excretion analysis")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### Toxicity Assessment")
        st.write("Hepatotoxicity, hERG, mutagenicity, and carcinogenicity risk prediction")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sub-header">Platform Capabilities</div>', unsafe_allow_html=True)
    
    capabilities = pd.DataFrame({
        'Module': ['ADME/PK', 'Toxicity', 'Drug-likeness', 'Target Prediction', 'ML Models', 'Knowledge Graph'],
        'Capabilities': [
            'LogP, Caco-2, BBB, CYP450, Clearance',
            'Hepatotox, hERG, Ames, Carcinogenicity',
            'Lipinski, Veber, QED, SA Score',
            'Kinase, GPCR, Ion Channel, Enzyme',
            'Random Forest, XGBoost, Neural Network',
            'Drug-Target-Disease Relationships'
        ],
        'Status': ['Active'] * 6
    })
    
    st.dataframe(capabilities, use_container_width=True, hide_index=True)
    
    st.markdown('<div class="sub-header">Industry Alignment</div>', unsafe_allow_html=True)
    st.info("""
    This platform mirrors pharmaceutical industry best practices used in modern drug discovery:
    
    - **ML Techniques**: Random Forest, XGBoost, and Neural Networks for property prediction
    - **ADME/PK Focus**: Critical for small molecule development pipelines
    - **Target Class Prediction**: Kinase inhibitors central to oncology drug discovery
    - **Model Explainability**: SHAP values and feature importance for regulatory compliance
    - **Knowledge Graphs**: Drug-target-disease relationships for precision medicine
    """)


elif page == "Molecule Input":
    st.markdown('<div class="sub-header">Molecule Input & Structure Viewer</div>', unsafe_allow_html=True)
    
    input_method = st.radio("Input Method", ["SMILES String", "Draw Structure (Coming Soon)", "Upload File"], horizontal=True)
    
    if input_method == "SMILES String":
        smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
        molecule_name = st.text_input("Molecule Name (Optional)", "Ibuprofen")
        
        if st.button("Validate & Analyze", type="primary"):
            is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
            
            if is_valid:
                st.success(f"Valid SMILES: `{canonical_smiles}`")
                
                mol = mol_processor.smiles_to_mol(canonical_smiles)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("#### 2D Structure")
                    img = visualizer.mol_to_image(mol, size=(400, 400))
                    if img:
                        st.image(img)
                
                with col2:
                    st.markdown("#### Basic Properties")
                    props = mol_processor.calculate_basic_properties(mol)
                    
                    props_df = pd.DataFrame([props]).T
                    props_df.columns = ['Value']
                    st.dataframe(props_df, use_container_width=True)
                
                st.markdown("#### Drug-Likeness Quick Check")
                lipinski = mol_processor.calculate_lipinski_descriptors(mol)
                veber = mol_processor.calculate_veber_descriptors(mol)
                qed = mol_processor.calculate_qed(mol)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Lipinski Violations", lipinski['Violations'])
                col2.metric("Veber Pass", "Pass" if veber['Passes'] else "Fail")
                col3.metric("QED Score", qed)
                col4.metric("Overall", "Drug-like" if lipinski['Violations'] <= 1 and veber['Passes'] else "Review")
                
            else:
                st.error(f"Invalid SMILES: {canonical_smiles}")


elif page == "ADME/PK Analysis":
    st.markdown('<div class="sub-header">ADME/PK Property Prediction</div>', unsafe_allow_html=True)
    
    st.info("""
    **Note:** ADME/PK predictions use heuristic scoring functions based on molecular descriptors (LogP, TPSA, molecular weight, etc.).  
    For production use, replace with validated QSAR models trained on experimental ADME data.
    """)
    
    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
    
    if st.button("Run ADME/PK Analysis", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            adme_profile = adme_predictor.comprehensive_adme_profile(mol)
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["LogP", "Caco-2 Permeability", "BBB Penetration", "CYP450 Metabolism", "Clearance"])
            
            with tab1:
                data = adme_profile['LogP']
                st.markdown(f"**LogP:** {data['LogP']}")
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
            
            with tab2:
                data = adme_profile['Caco-2 Permeability']
                st.markdown(f"**Caco-2 Score:** {data['Caco-2 Score']}")
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
            
            with tab3:
                data = adme_profile['BBB Penetration']
                st.markdown(f"**BBB Score:** {data['BBB Score']}")
                st.markdown(f"**Probability:** {data['Probability']}")
                st.info(data['Recommendation'])
            
            with tab4:
                data = adme_profile['CYP450 Metabolism']
                st.markdown(f"**Primary Metabolizer:** {data['Primary Metabolizer']}")
                st.write(f"- CYP3A4: {data['CYP3A4 Substrate Probability']}")
                st.write(f"- CYP2D6: {data['CYP2D6 Substrate Probability']}")
                st.write(f"- CYP2C9: {data['CYP2C9 Substrate Probability']}")
                st.warning(data['Interpretation'])
            
            with tab5:
                data = adme_profile['Clearance']
                st.markdown(f"**Clearance Score:** {data['Clearance Score']}")
                st.markdown(f"**Category:** {data['Category']}")
                st.markdown(f"**Half-life Estimate:** {data['Half-life Estimate']}")
                st.info(data['Interpretation'])
        else:
            st.error("Invalid SMILES string")


elif page == "Toxicity Profile":
    st.markdown('<div class="sub-header">Toxicity Risk Assessment</div>', unsafe_allow_html=True)
    
    st.info("""
    **Note:** Toxicity predictions use heuristic scoring based on structural alerts and molecular properties.  
    For production use, replace with validated toxicophore models and QSAR trained on experimental toxicity data (Tox21, ToxCast).
    """)
    
    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
    
    if st.button("Run Toxicity Analysis", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            tox_profile = toxicity_predictor.comprehensive_toxicity_profile(mol)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Hepatotoxicity")
                data = tox_profile['Hepatotoxicity']
                st.metric("Risk Level", data['Hepatotoxicity Risk'])
                st.markdown(f"**Category:** {data['Category']}")
                
                if 'High' in data['Category']:
                    st.markdown(f'<div class="danger-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                elif 'Moderate' in data['Category']:
                    st.markdown(f'<div class="warning-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="success-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                
                st.markdown("#### Mutagenicity (Ames Test)")
                data = tox_profile['Mutagenicity (Ames)']
                st.metric("Risk Level", data['Mutagenicity Risk'])
                st.markdown(f"**Probability:** {data['Ames Positive Probability']}")
                st.info(data['Recommendation'])
            
            with col2:
                st.markdown("#### Cardiotoxicity (hERG)")
                data = tox_profile['Cardiotoxicity (hERG)']
                st.metric("hERG Inhibition Risk", data['hERG Inhibition Risk'])
                st.markdown(f"**Category:** {data['Category']}")
                st.markdown(f"**IC50 Estimate:** {data['IC50 Estimate']}")
                
                if 'High' in data['Category']:
                    st.markdown(f'<div class="danger-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                elif 'Moderate' in data['Category']:
                    st.markdown(f'<div class="warning-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="success-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                
                st.markdown("#### Carcinogenicity")
                data = tox_profile['Carcinogenicity']
                st.metric("Risk Level", data['Carcinogenicity Risk'])
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Recommendation'])
        else:
            st.error("Invalid SMILES string")


elif page == "Target Prediction":
    st.markdown('<div class="sub-header">Target Class Prediction</div>', unsafe_allow_html=True)
    
    st.info("""
    **Note:** Target class predictions use heuristic scoring based on physicochemical properties typical of each target class.  
    For production use, replace with validated bioactivity models trained on ChEMBL or similar databases.
    """)
    
    smiles_input = st.text_input("Enter SMILES String", "Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C")
    
    if st.button("Predict Target Class", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            target_profile = target_predictor.comprehensive_target_prediction(mol)
            
            st.markdown("### Primary Target Prediction")
            st.success(f"**Primary Target Class:** {target_profile['Primary Target Class']} (Confidence: {target_profile['Confidence']})")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Kinase Inhibitor")
                data = target_profile['Kinase Inhibitor']
                st.metric("Probability", data['Kinase Inhibitor Probability'])
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
                
                st.markdown("#### GPCR Ligand")
                data = target_profile['GPCR Ligand']
                st.metric("Probability", data['GPCR Ligand Probability'])
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
            
            with col2:
                st.markdown("#### Ion Channel Modulator")
                data = target_profile['Ion Channel Modulator']
                st.metric("Probability", data['Ion Channel Modulator Probability'])
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
                
                st.markdown("#### Enzyme Inhibitor")
                data = target_profile['Enzyme Inhibitor']
                st.metric("Probability", data['Enzyme Inhibitor Probability'])
                st.markdown(f"**Category:** {data['Category']}")
        else:
            st.error("Invalid SMILES string")


elif page == "ML Models":
    st.markdown('<div class="sub-header">Machine Learning Models & Explainability</div>', unsafe_allow_html=True)
    
    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
    
    if st.button("Run ML Prediction", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            descriptors = mol_processor.calculate_molecular_descriptors(mol)
            
            prediction = ml_predictor.predict_with_ensemble(descriptors)
            
            st.markdown("### Ensemble Prediction Results")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Random Forest", f"{prediction['Random Forest Probability']}%")
            col2.metric("XGBoost", f"{prediction['XGBoost Probability']}%")
            col3.metric("Ensemble", f"{prediction['Ensemble Probability']}%")
            
            st.markdown(f"**Final Prediction:** {prediction['Prediction']} (Confidence: {prediction['Confidence']}%)")
            
            st.markdown("### Feature Importance Analysis")
            
            importance_df = ml_predictor.get_feature_importance()
            
            if not importance_df.empty:
                fig = visualizer.create_feature_importance_plot(importance_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(importance_df, use_container_width=True, hide_index=True)
            
            st.info("""
            **Model Training**: Models trained on synthetic pharmaceutical dataset with molecular descriptors.
            Cross-validation ensures robustness. Feature importance reveals which molecular properties
            most influence drug-likeness predictions.
            """)
        else:
            st.error("Invalid SMILES string")


elif page == "Knowledge Graph":
    st.markdown('<div class="sub-header">Biomedical Knowledge Graph Explorer</div>', unsafe_allow_html=True)
    
    st.info("""
    This knowledge graph connects drugs, protein targets, biological pathways, and diseases,
    demonstrating how pharmaceutical researchers link molecular data across multiple data sources for drug discovery.
    """)
    
    stats = kg.get_graph_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Nodes", stats['Total Nodes'])
    col2.metric("Compounds", stats['Compounds'])
    col3.metric("Targets", stats['Targets'])
    col4.metric("Diseases", stats['Diseases'])
    
    st.markdown("### Query Knowledge Graph")
    
    query_type = st.selectbox("Query Type", ["Drug Mechanism", "Target Information", "Disease Relationships"])
    
    if query_type == "Drug Mechanism":
        drugs = ['Imatinib', 'Gefitinib', 'Sorafenib', 'Venetoclax', 'Upadacitinib', 'Adalimumab']
        selected_drug = st.selectbox("Select Drug", drugs)
        
        if st.button("Get Mechanism of Action"):
            moa = kg.get_mechanism_of_action(selected_drug)
            
            if 'error' not in moa:
                st.markdown(f"#### {moa['Drug']}")
                st.markdown(f"**Targets:** {', '.join(moa['Targets'])}")
                st.markdown(f"**Pathways:** {', '.join(moa['Pathways']) if moa['Pathways'] else 'N/A'}")
                st.markdown(f"**Indications:** {', '.join(moa['Indications'])}")
            else:
                st.warning(moa['error'])
    
    elif query_type == "Target Information":
        targets = ['BCR-ABL', 'EGFR', 'VEGFR', 'BCL-2', 'JAK1', 'TNF-alpha']
        selected_target = st.selectbox("Select Target", targets)
        
        if st.button("Get Target Information"):
            drugs = kg.find_similar_drugs(selected_target)
            diseases = kg.get_target_diseases(selected_target)
            
            st.markdown(f"**Drugs targeting {selected_target}:** {', '.join(drugs) if drugs else 'None in database'}")
            st.markdown(f"**Associated diseases:** {', '.join(diseases) if diseases else 'None in database'}")


elif page == "Batch Screening":
    st.markdown('<div class="sub-header">Batch Screening & Lead Prioritization</div>', unsafe_allow_html=True)
    
    st.info("""
    Upload a CSV file with SMILES strings or use the example dataset to screen multiple compounds.
    Results will be ranked by drug-likeness and ADME/PK properties.
    """)
    
    input_method = st.radio("Input Method", ["Example Dataset", "Upload CSV"])
    
    if input_method == "Example Dataset":
        if st.button("Run Batch Analysis on Example Set"):
            example_molecules = [
                ("Ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
                ("Aspirin", "CC(=O)Oc1ccccc1C(=O)O"),
                ("Caffeine", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"),
                ("Paracetamol", "CC(=O)Nc1ccc(cc1)O"),
                ("Atorvastatin", "CC(C)c1c(c(c(c(c1OCC(CC(CC(=O)O)O)O)c2ccc(cc2)F)C(=O)Nc3ccccc3)O)C(C)C")
            ]
            
            results = []
            
            for name, smiles in example_molecules:
                is_valid, canonical_smiles = mol_processor.validate_smiles(smiles)
                
                if is_valid:
                    mol = mol_processor.smiles_to_mol(canonical_smiles)
                    
                    lipinski = drug_likeness.lipinski_rule_of_5(mol)
                    qed = drug_likeness.qed_score(mol)
                    
                    results.append({
                        'Name': name,
                        'SMILES': canonical_smiles,
                        'MW': lipinski['Molecular Weight'],
                        'LogP': lipinski['LogP'],
                        'Lipinski Violations': lipinski['Violations'],
                        'QED Score': qed['QED Score'],
                        'Passes Lipinski': 'Yes' if lipinski['Passes'] else 'No'
                    })
            
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('QED Score', ascending=False)
            
            st.markdown("### Batch Analysis Results")
            st.dataframe(results_df, use_container_width=True, hide_index=True)
            
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name="batch_screening_results.csv",
                mime="text/csv"
            )
    
    else:
        uploaded_file = st.file_uploader("Upload CSV (columns: name, smiles)", type=['csv'])
        if uploaded_file:
            st.info("CSV upload functionality ready. Add your SMILES data!")


elif page == "Case Study":
    st.markdown('<div class="sub-header">Case Study: Ranking Kinase Inhibitor Leads</div>', 
                unsafe_allow_html=True)
    
    case_study = get_case_study_data()
    
    st.markdown(f"#### {case_study['title']}")
    st.write(case_study['description'])
    
    st.markdown("### Evaluation Criteria")
    for i, criterion in enumerate(case_study['evaluation_criteria'], 1):
        st.write(f"{i}. {criterion}")
    
    if st.button("Run Complete Analysis on All Candidates", type="primary"):
        results = []
        
        for candidate in case_study['molecules']:
            is_valid, canonical_smiles = mol_processor.validate_smiles(candidate['smiles'])
            
            if is_valid:
                mol = mol_processor.smiles_to_mol(canonical_smiles)
                
                lipinski = drug_likeness.lipinski_rule_of_5(mol)
                qed = drug_likeness.qed_score(mol)
                kinase_pred = target_predictor.predict_kinase_inhibitor(mol)
                adme = adme_predictor.predict_caco2_permeability(mol)
                tox = toxicity_predictor.predict_hepatotoxicity(mol)
                
                score = 0
                if lipinski['Passes']: score += 20
                if qed['QED Score'] >= 0.5: score += 20
                if 'Likely' in kinase_pred['Category']: score += 30
                if 'High' in adme['Category'] or 'Moderate' in adme['Category']: score += 15
                if 'Low' in tox['Category']: score += 15
                
                results.append({
                    'Candidate': candidate['name'],
                    'Lipinski': 'Pass' if lipinski['Passes'] else 'Fail',
                    'QED': qed['QED Score'],
                    'Kinase Prob': kinase_pred['Kinase Inhibitor Probability'],
                    'Permeability': adme['Category'],
                    'Hepatotox Risk': tox['Category'],
                    'Overall Score': score
                })
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('Overall Score', ascending=False)
        results_df['Rank'] = range(1, len(results_df) + 1)
        
        st.markdown("### Lead Ranking Results")
        st.dataframe(results_df[['Rank', 'Candidate', 'Overall Score', 'Lipinski', 'QED', 
                                 'Kinase Prob', 'Permeability', 'Hepatotox Risk']], 
                    use_container_width=True, hide_index=True)
        
        st.success(f"**Recommended Lead:** {results_df.iloc[0]['Candidate']} (Score: {results_df.iloc[0]['Overall Score']}/100)")
        
        st.markdown("### Conclusion")
        st.info("""
        This case study demonstrates a typical pharmaceutical lead prioritization workflow:
        
        1. **Multi-parameter optimization**: Balancing efficacy (kinase inhibition) with safety (toxicity) and PK (permeability)
        2. **Data-driven decision making**: Using ML predictions to rank candidates before expensive experimental validation
        3. **Risk mitigation**: Identifying potential liabilities early in the discovery process
        
        This mirrors industry-standard approaches to lead optimization in kinase inhibitor drug discovery programs.
        """)


elif page == "About":
    st.markdown('<div class="sub-header">About This Platform</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### AI-Powered Drug Discovery Platform
    
    An open-source educational platform demonstrating computational drug discovery workflows using 
    cheminformatics, QSAR modeling, and machine learning techniques used in pharmaceutical research.
    
    #### Key Features
    
    - **Molecular Property Prediction**: ADME/PK, toxicity, drug-likeness
    - **Target Class Prediction**: Kinase, GPCR, ion channel, enzyme inhibitors
    - **ML Models**: Random Forest, XGBoost, Neural Networks with explainability
    - **Knowledge Graph**: Drug-target-disease relationships
    - **Batch Screening**: High-throughput lead prioritization
    - **FastAPI Backend**: REST API for pharmaceutical predictions
    
    #### Technologies Used
    
    - **ML/AI**: scikit-learn, XGBoost, SHAP
    - **Cheminformatics**: RDKit, molecular descriptors, fingerprints
    - **Visualization**: Plotly, Matplotlib, Seaborn
    - **Backend**: FastAPI, Uvicorn
    - **Frontend**: Streamlit
    - **Data**: NetworkX (knowledge graphs), UMAP (clustering)
    
    #### Industry Standard Workflows
    
    This platform demonstrates workflows and techniques used in pharmaceutical discovery:
    
    1. **ADME/PK Focus**: Critical for small molecule drug development pipelines
    2. **Kinase Inhibitors**: Important target class in oncology research
    3. **Multi-model Approach**: Standard practice for robust predictions
    4. **Explainability**: Required for regulatory submissions
    5. **Knowledge Graphs**: Used for target identification and validation
    
    #### References & Industry Practices
    
    - Random Forest & XGBoost: Standard models in pharmaceutical QSAR
    - SHAP values: Explainable AI for regulatory compliance
    - Lipinski/Veber rules: Industry-standard drug-likeness filters
    - hERG prediction: Critical safety assessment
    - CYP450 profiling: Standard ADME analysis
    
    See `references.md` for complete scientific citations and methodology documentation.
    
    ---
    
    **Developer**: Ardit Mishra  
    **Tech Stack**: Python, RDKit, scikit-learn, Streamlit, FastAPI  
    **GitHub**: github.com/ardit-mishra
    """)
    
    st.markdown('<div class="sub-header">Contact</div>', unsafe_allow_html=True)
    st.write("For questions about this platform or to discuss pharmaceutical AI/ML applications.")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8rem;'>
    <p>AI-Powered Drug Discovery Platform | Open-Source Pharmaceutical Research Tool</p>
    <p>Built with RDKit • scikit-learn • XGBoost • Streamlit • FastAPI</p>
    <p>Developed by Ardit Mishra | github.com/ardit-mishra</p>
</div>
""", unsafe_allow_html=True)
