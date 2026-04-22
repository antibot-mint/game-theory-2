import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
import time
import random
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import io

st.set_page_config(page_title="⚖️ eBay vs AT&T Classroom Game")

st.title("⚖️ eBay vs AT&T Lawsuit Game")

# -------------------- Firebase Setup --------------------
try:
    database_url = st.secrets["database_url"]
    service_account = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"],
    }
    if not firebase_admin._apps:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred, {"databaseURL": database_url})
except KeyError:
    st.error("🔥 Firebase secrets not configured.")
    st.stop()

# -------------------- Helper Functions --------------------
def plot_enhanced_percentage_bar(choices, labels, title, player_type):
    if len(choices) > 0:
        counts = pd.Series(choices).value_counts(normalize=True).reindex(labels, fill_value=0) * 100
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#f0f0f0')
        ax.set_facecolor('#e0e0e0')
        colors_scheme = ['#e74c3c', '#3498db'] if player_type == "eBay" else ['#3498db', '#e74c3c']
        bars = counts.plot(kind='bar', ax=ax, color=colors_scheme, linewidth=2, width=0.7)
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel("Percentage (%)", fontsize=14)
        ax.set_xlabel("Choice", fontsize=14)
        ax.tick_params(rotation=0, labelsize=12)
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        for i, bar in enumerate(ax.patches):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')
        ax.text(0.02, 0.98, f"Sample size: {len(choices)} participants",
                transform=ax.transAxes, fontsize=10, verticalalignment='top', alpha=0.7,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        today = datetime.today().strftime('%B %d, %Y')
        ax.text(0.98, 0.98, f"Generated: {today}", transform=ax.transAxes,
                fontsize=10, verticalalignment='top', horizontalalignment='right', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning(f"⚠ No data available for {title}")

def create_pdf_report():
    from matplotlib.backends.backend_pdf import PdfPages
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    with PdfPages(temp_file.name) as pdf:
        all_matches = db.reference("lawsuit_matches").get() or {}
        results_data = []
        for match_id, match_data in all_matches.items():
            if "ebay_response" in match_data and "att_response" in match_data:
                guilt = match_data["ebay_guilt"]
                offer = match_data["ebay_response"]
                response = match_data["att_response"]
                if guilt == "Guilty":
                    if offer == "Generous" and response == "Accept":
                        ebay_payoff, att_payoff = -200, 200
                    elif offer == "Stingy" and response == "Accept":
                        ebay_payoff, att_payoff = -20, 20
                    else:  # Stingy + Reject
                        ebay_payoff, att_payoff = -320, 300
                else:  # Innocent
                    if offer == "Generous" and response == "Accept":
                        ebay_payoff, att_payoff = -200, 200
                    elif offer == "Stingy" and response == "Accept":
                        ebay_payoff, att_payoff = -20, 20
                    else:  # Stingy + Reject
                        ebay_payoff, att_payoff = 0, -20
                results_data.append({
                    "Match_ID": match_id,
                    "eBay_Player": match_data["ebay_player"],
                    "ATT_Player": match_data["att_player"],
                    "eBay_Status": guilt,
                    "Offer": offer,
                    "Response": response,
                    "eBay_Payoff": ebay_payoff,
                    "ATT_Payoff": att_payoff
                })
        if results_data:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('AT&T vs eBay Lawsuit Game - Complete Results', fontsize=20, fontweight='bold')
            ebay_offers = [r["Offer"] for r in results_data]
            att_responses = [r["Response"] for r in results_data]
            guilt_statuses = [r["eBay_Status"] for r in results_data]
            offer_counts = pd.Series(ebay_offers).value_counts(normalize=True) * 100
            ax1.bar(offer_counts.index, offer_counts.values, color=['#e74c3c', '#3498db'], alpha=0.8)
            ax1.set_title('eBay Settlement Offers', fontweight='bold')
            ax1.set_ylabel('Percentage (%)')
            ax1.set_ylim(0, 100)
            for i, v in enumerate(offer_counts.values):
                ax1.text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')
            ax1.grid(True, alpha=0.3)
            response_counts = pd.Series(att_responses).value_counts(normalize=True) * 100
            ax2.bar(response_counts.index, response_counts.values, color=['#3498db', '#e74c3c'], alpha=0.8)
            ax2.set_title('AT&T Responses', fontweight='bold')
            ax2.set_ylabel('Percentage (%)')
            ax2.set_ylim(0, 100)
            for i, v in enumerate(response_counts.values):
                ax2.text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            guilt_counts = pd.Series(guilt_statuses).value_counts(normalize=True) * 100
            ax3.bar(guilt_counts.index, guilt_counts.values, color=['#e74c3c', '#2ecc71'], alpha=0.8)
            ax3.set_title('eBay Guilt Distribution', fontweight='bold')
            ax3.set_ylabel('Percentage (%)')
            ax3.set_ylim(0, 100)
            for i, v in enumerate(guilt_counts.values):
                ax3.text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')
            ax3.grid(True, alpha=0.3)
            strategies = []
            for r in results_data:
                if r["eBay_Status"] == "Innocent" and r["Offer"] == "Stingy":
                    strategies.append("Separating")
                elif r["eBay_Status"] == "Guilty" and r["Offer"] == "Generous":
                    strategies.append("Separating")
                else:
                    strategies.append("Pooling")
            if strategies:
                strategy_counts = pd.Series(strategies).value_counts(normalize=True) * 100
                ax4.bar(strategy_counts.index, strategy_counts.values, color=['#9b59b6', '#f39c12'], alpha=0.8)
                ax4.set_title('eBay Strategy Analysis', fontweight='bold')
                ax4.set_ylabel('Percentage (%)')
                ax4.set_ylim(0, 100)
                for i, v in enumerate(strategy_counts.values):
                    ax4.text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')
                ax4.grid(True, alpha=0.3)
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight', dpi=300)
            plt.close(fig)
            # Detailed table
            fig, ax = plt.subplots(figsize=(16, 10))
            ax.axis('tight')
            ax.axis('off')
            table_data = [["Match ID", "eBay Player", "AT&T Player", "eBay Status", "Offer", "Response", "eBay Payoff", "AT&T Payoff"]]
            for r in results_data:
                table_data.append([
                    r["Match_ID"], r["eBay_Player"], r["ATT_Player"],
                    r["eBay_Status"], r["Offer"], r["Response"],
                    str(r["eBay_Payoff"]), str(r["ATT_Payoff"])
                ])
            table = ax.table(cellText=table_data[1:], colLabels=table_data[0],
                           cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)
            for i in range(len(table_data[0])):
                table[(0, i)].set_facecolor('#4472C4')
                table[(0, i)].set_text_props(weight='bold', color='white')
            ax.set_title('Detailed Game Results', fontsize=16, fontweight='bold', pad=20)
            pdf.savefig(fig, bbox_inches='tight', dpi=300)
            plt.close(fig)
    with open(temp_file.name, 'rb') as f:
        pdf_content = f.read()
    import os
    os.unlink(temp_file.name)
    return pdf_content

def export_payoffs_csv():
    """Export all completed matches to a CSV string"""
    all_matches = db.reference("lawsuit_matches").get() or {}
    rows = []
    for match_id, match_data in all_matches.items():
        if "ebay_response" in match_data and "att_response" in match_data:
            guilt = match_data["ebay_guilt"]
            offer = match_data["ebay_response"]
            response = match_data["att_response"]
            if guilt == "Guilty":
                if offer == "Generous" and response == "Accept":
                    ebay_payoff, att_payoff = -200, 200
                elif offer == "Stingy" and response == "Accept":
                    ebay_payoff, att_payoff = -20, 20
                else:
                    ebay_payoff, att_payoff = -320, 300
            else:
                if offer == "Generous" and response == "Accept":
                    ebay_payoff, att_payoff = -200, 200
                elif offer == "Stingy" and response == "Accept":
                    ebay_payoff, att_payoff = -20, 20
                else:
                    ebay_payoff, att_payoff = 0, -20
            rows.append({
                "Match ID": match_id,
                "eBay Player": match_data["ebay_player"],
                "AT&T Player": match_data["att_player"],
                "eBay Status (Guilty/Innocent)": guilt,
                "eBay Offer": offer,
                "AT&T Response": response,
                "eBay Payoff": ebay_payoff,
                "AT&T Payoff": att_payoff
            })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)

# -------------------- Admin Panel --------------------
admin_password = st.text_input("Admin Password:", type="password")
if admin_password == "admin123":
    st.header("🎓 Admin Control Panel")
    try:
        all_players_raw = db.reference("lawsuit_players").get()
        all_players = all_players_raw if isinstance(all_players_raw, dict) else {}
        all_matches_raw = db.reference("lawsuit_matches").get()
        all_matches = all_matches_raw if isinstance(all_matches_raw, dict) else {}
        expected_players = db.reference("lawsuit_expected_players").get() or 0
    except Exception as e:
        st.error("Error connecting to database. Please refresh the page.")
        all_players = {}
        all_matches = {}
        expected_players = 0

    total_registered = len(all_players)
    ebay_players = [p for p in all_players.values() if p and p.get("role") == "eBay"]
    att_players = [p for p in all_players.values() if p and p.get("role") == "AT&T"]
    completed_matches = 0
    for match_data in all_matches.values():
        if match_data and "ebay_response" in match_data and "att_response" in match_data:
            completed_matches += 1

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Expected Players", expected_players)
    with col2: st.metric("Registered Players", total_registered)
    with col3: st.metric("eBay Players", len(ebay_players))
    with col4: st.metric("AT&T Players", len(att_players))
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Matches", len(all_matches))
    with col2: st.metric("Completed Matches", completed_matches)
    with col3:
        guilty_count = len([p for p in ebay_players if p.get("guilt_status") == "Guilty"])
        st.metric("Guilty eBay Players", guilty_count)

    st.subheader("👥 Player Activity Monitor")
    if all_players:
        player_status = []
        for name, player_data in all_players.items():
            role = player_data.get("role", "Unknown")
            status = "🔴 Registered"
            activity = "Waiting for match"
            paired_with = "Not yet matched"
            player_match = None
            for match_id, match_data in all_matches.items():
                if name in [match_data.get("ebay_player"), match_data.get("att_player")]:
                    player_match = match_data
                    break
            if player_match:
                if role == "eBay":
                    paired_with = player_match.get("att_player", "Unknown")
                    if "ebay_response" in player_match:
                        status = "🟢 Completed"
                        activity = f"Offered: {player_match['ebay_response']}"
                    else:
                        status = "🟡 In Match"
                        activity = "Making offer..."
                elif role == "AT&T":
                    paired_with = player_match.get("ebay_player", "Unknown")
                    if "att_response" in player_match:
                        status = "🟢 Completed"
                        activity = f"Response: {player_match['att_response']}"
                    else:
                        status = "🟡 In Match"
                        activity = "Waiting for eBay offer..."
            extra_info = f"({player_data.get('guilt_status', 'Unknown')})" if role == "eBay" else ""
            player_status.append({
                "Player Name": name,
                "Role": role,
                "Paired With": paired_with,
                "Status": status,
                "Activity": activity,
                "Extra Info": extra_info
            })
        st.dataframe(pd.DataFrame(player_status), use_container_width=True)

    st.subheader("📈 Live Game Analytics")
    if completed_matches > 0:
        ebay_offers = []
        att_responses = []
        guilt_statuses = []
        for match_data in all_matches.values():
            if match_data and "ebay_response" in match_data and "att_response" in match_data:
                ebay_offers.append(match_data["ebay_response"])
                att_responses.append(match_data["att_response"])
                guilt_statuses.append(match_data["ebay_guilt"])
        col1, col2 = st.columns(2)
        with col1:
            plot_enhanced_percentage_bar(ebay_offers, ["Generous", "Stingy"], "eBay Settlement Offers", "eBay")
            plot_enhanced_percentage_bar(guilt_statuses, ["Guilty", "Innocent"], "eBay Guilt Distribution", "eBay")
        with col2:
            plot_enhanced_percentage_bar(att_responses, ["Accept", "Reject"], "AT&T Responses", "AT&T")
            strategies = []
            for match_data in all_matches.values():
                if match_data and "ebay_response" in match_data and "att_response" in match_data:
                    guilt = match_data["ebay_guilt"]
                    offer = match_data["ebay_response"]
                    if guilt == "Innocent" and offer == "Stingy":
                        strategies.append("Separating")
                    elif guilt == "Guilty" and offer == "Generous":
                        strategies.append("Separating")
                    else:
                        strategies.append("Pooling")
            if strategies:
                plot_enhanced_percentage_bar(strategies, ["Pooling", "Separating"], "eBay Strategy Analysis", "eBay")
    else:
        st.info("No completed matches yet. Charts will appear when players start completing games.")

    st.subheader("⚙️ Game Configuration")
    current_expected = db.reference("lawsuit_expected_players").get() or 0
    st.write(f"Current expected players: {current_expected}")
    new_expected_players = st.number_input("Set expected number of players:", min_value=0, max_value=100, value=current_expected, step=2, help="Must be an even number (players are paired)")
    if st.button("⚙ Update Expected Players"):
        if new_expected_players % 2 == 0:
            db.reference("lawsuit_expected_players").set(new_expected_players)
            st.success(f"✅ Expected players set to {new_expected_players}")
            st.rerun()
        else:
            st.error("⚠ Number of players must be even (for pairing)")

    st.subheader("🔒 Registration Limit")
    registrations_full = db.reference("lawsuit_registrations_full").get() or False
    if registrations_full:
        st.warning(f"🚫 Registrations are automatically locked because {total_registered} players have registered (expected: {expected_players}). New players cannot join.")
        if st.button("🔓 Force Unlock (allow more registrations)"):
            db.reference("lawsuit_registrations_full").set(False)
            st.success("Registration limit reset. New players can now join until the expected number is reached again.")
            st.rerun()
    else:
        if total_registered >= expected_players and expected_players > 0:
            st.warning(f"⚠️ Registered players ({total_registered}) have reached or exceeded expected players ({expected_players}). New registrations will be blocked automatically.")
            db.reference("lawsuit_registrations_full").set(True)
            st.rerun()
        else:
            st.info(f"✅ Registrations open. {total_registered}/{expected_players} registered. New players can join.")

    st.subheader("🎲 Role Management")
    if total_registered >= 2 and total_registered % 2 == 0:
        if st.button("👥 Assign Roles (randomly half eBay, half AT&T)"):
            db.reference("lawsuit_matches").delete()
            for pname in all_players.keys():
                db.reference(f"lawsuit_players/{pname}/role").delete()
                db.reference(f"lawsuit_players/{pname}/guilt_status").delete()
                db.reference(f"lawsuit_players/{pname}/matched").delete()
            player_names = list(all_players.keys())
            random.shuffle(player_names)
            half = total_registered // 2
            ebay_names = player_names[:half]
            att_names = player_names[half:]
            for pname in ebay_names:
                is_guilty = random.random() < 0.25
                guilt_status = "Guilty" if is_guilty else "Innocent"
                db.reference(f"lawsuit_players/{pname}").update({"role": "eBay", "guilt_status": guilt_status})
            for pname in att_names:
                db.reference(f"lawsuit_players/{pname}").update({"role": "AT&T"})
            db.reference("lawsuit_roles_assigned").set(True)
            db.reference("lawsuit_matching_done").set(False)
            st.success(f"✅ Roles assigned: {len(ebay_names)} eBay, {len(att_names)} AT&T")
            st.rerun()
    else:
        st.info(f"Need at least 2 registered players and an even number to assign roles. Currently {total_registered} players.")

    if st.button("🔄 Reassign Roles (clear and reassign)"):
        for pname in all_players.keys():
            db.reference(f"lawsuit_players/{pname}/role").delete()
            db.reference(f"lawsuit_players/{pname}/guilt_status").delete()
            db.reference(f"lawsuit_players/{pname}/matched").delete()
        db.reference("lawsuit_roles_assigned").delete()
        db.reference("lawsuit_matches").delete()
        db.reference("lawsuit_matching_done").set(False)
        st.success("Roles cleared. Click 'Assign Roles' again when ready.")
        st.rerun()

    if st.button("🤝 Start Matching (pair each eBay with a unique AT&T)"):
        db.reference("lawsuit_matches").delete()
        for pname in all_players.keys():
            db.reference(f"lawsuit_players/{pname}/matched").delete()
        all_players_data = db.reference("lawsuit_players").get() or {}
        ebay_players_list = [p for p, data in all_players_data.items() if data.get("role") == "eBay"]
        att_players_list = [p for p, data in all_players_data.items() if data.get("role") == "AT&T"]
        if len(ebay_players_list) != len(att_players_list):
            st.error(f"Mismatch: {len(ebay_players_list)} eBay, {len(att_players_list)} AT&T. Please reassign roles first.")
        else:
            random.shuffle(ebay_players_list)
            random.shuffle(att_players_list)
            pairs = list(zip(ebay_players_list, att_players_list))
            for ebay, att in pairs:
                match_id = f"{ebay}_vs_{att}"
                db.reference(f"lawsuit_matches/{match_id}").set({
                    "ebay_player": ebay,
                    "att_player": att,
                    "ebay_guilt": all_players_data[ebay].get("guilt_status"),
                    "timestamp": time.time()
                })
                db.reference(f"lawsuit_players/{ebay}/matched").set(True)
                db.reference(f"lawsuit_players/{att}/matched").set(True)
            db.reference("lawsuit_matching_done").set(True)
            st.success(f"✅ Created {len(pairs)} unique pairs. Players can now see their matches.")
            st.rerun()

    st.subheader("🗂️ Data Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Export Results (PDF)"):
            if completed_matches > 0:
                with st.spinner("Generating PDF report..."):
                    try:
                        pdf_content = create_pdf_report()
                        st.download_button(label="📥 Download PDF Report", data=pdf_content, file_name="lawsuit_game_results.pdf", mime="application/pdf")
                        st.success("✅ PDF report generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        csv_data = export_payoffs_csv()
                        st.download_button(label="📥 Download CSV (Fallback)", data=csv_data, file_name="lawsuit_game_results.csv", mime="text/csv")
            else:
                st.warning("No completed matches to export.")
        if st.button("📊 Export Payoffs to CSV"):
            if completed_matches > 0:
                csv_data = export_payoffs_csv()
                st.download_button(label="📥 Download CSV File", data=csv_data, file_name="lawsuit_payoffs.csv", mime="text/csv")
            else:
                st.warning("No completed matches to export.")
    with col2:
        if st.button("🗑️ Clear All Game Data"):
            db.reference("lawsuit_players").delete()
            db.reference("lawsuit_matches").delete()
            db.reference("lawsuit_expected_players").set(0)
            db.reference("lawsuit_roles_assigned").delete()
            db.reference("lawsuit_matching_done").delete()
            db.reference("lawsuit_registrations_full").delete()
            st.success("🧹 ALL game data cleared!")
            st.rerun()

    if expected_players > 0 and completed_matches < (expected_players // 2):
        time.sleep(3)
        st.rerun()
    elif completed_matches >= (expected_players // 2) and expected_players > 0:
        st.success("🎉 All matches completed! Game finished.")
        st.header("📊 Admin View: Summary Analysis - Class Results vs Game Theory")
        ebay_offers = []
        att_responses = []
        guilt_statuses = []
        guilty_offers = []
        innocent_offers = []
        stingy_responses = []
        for match_data in all_matches.values():
            if match_data and "ebay_response" in match_data and "att_response" in match_data:
                guilt = match_data["ebay_guilt"]
                offer = match_data["ebay_response"]
                response = match_data["att_response"]
                ebay_offers.append(offer)
                att_responses.append(response)
                guilt_statuses.append(guilt)
                if guilt == "Guilty":
                    guilty_offers.append(offer)
                else:
                    innocent_offers.append(offer)
                if offer == "Stingy":
                    stingy_responses.append(response)
        st.subheader("🎯 Key Strategic Analysis")
        col1, col2 = st.columns(2)
        with col1:
            if guilty_offers and innocent_offers:
                guilty_stingy_pct = len([o for o in guilty_offers if o == "Stingy"]) / len(guilty_offers) * 100
                innocent_stingy_pct = len([o for o in innocent_offers if o == "Stingy"]) / len(innocent_offers) * 100
                fig, ax = plt.subplots(figsize=(8, 5))
                categories = ['Guilty eBay', 'Innocent eBay']
                percentages = [guilty_stingy_pct, innocent_stingy_pct]
                bars = ax.bar(categories, percentages, color=['#e74c3c', '#2ecc71'], alpha=0.8)
                ax.set_title("% Choosing Stingy Offer by eBay Type", fontsize=14, fontweight='bold')
                ax.set_ylabel("Percentage (%)")
                ax.set_ylim(0, 100)
                for bar, pct in zip(bars, percentages):
                    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2, f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("Need both guilty and innocent players to show this analysis")
        with col2:
            if stingy_responses:
                accept_pct = len([r for r in stingy_responses if r == "Accept"]) / len(stingy_responses) * 100
                fig, ax = plt.subplots(figsize=(8, 5))
                categories = ['Accept', 'Reject']
                accept_count = len([r for r in stingy_responses if r == "Accept"])
                reject_count = len([r for r in stingy_responses if r == "Reject"])
                percentages_vals = [accept_count/len(stingy_responses)*100, reject_count/len(stingy_responses)*100]
                bars = ax.bar(categories, percentages_vals, color=['#3498db', '#e74c3c'], alpha=0.8)
                ax.set_title("AT&T Responses to Stingy Offers", fontsize=14, fontweight='bold')
                ax.set_ylabel("Percentage (%)")
                ax.set_ylim(0, 100)
                for bar, pct in zip(bars, percentages_vals):
                    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2, f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("No stingy offers made yet")
        st.subheader("🧮 Game Theory Predictions vs Your Class")
        col1, col2, col3 = st.columns(3)
        with col1:
            if stingy_responses:
                accept_stingy_pct = len([r for r in stingy_responses if r == "Accept"]) / len(stingy_responses) * 100
                st.metric("AT&T Accept Stingy Offers", f"{accept_stingy_pct:.1f}%")
            else:
                st.metric("AT&T Accept Stingy Offers", "N/A")
        with col2:
            if guilty_offers:
                guilty_stingy_pct = len([o for o in guilty_offers if o == "Stingy"]) / len(guilty_offers) * 100
                st.metric("Guilty eBay Choose Stingy", f"{guilty_stingy_pct:.1f}%")
            else:
                st.metric("Guilty eBay Choose Stingy", "N/A")
        with col3:
            if innocent_offers:
                innocent_stingy_pct = len([o for o in innocent_offers if o == "Stingy"]) / len(innocent_offers) * 100
                st.metric("Innocent eBay Choose Stingy", f"{innocent_stingy_pct:.1f}%")
            else:
                st.metric("Innocent eBay Choose Stingy", "N/A")
        st.success("🎉 **Dynamic Signaling Game Complete!**")
        if st.button("🔄 Manual Refresh"):
            st.rerun()
    elif st.button("🔄 Refresh Dashboard"):
        st.rerun()
    st.divider()
    st.info("👨‍🏫 **Admin Dashboard**: Monitor game progress and analyze results in real-time.")
    st.stop()

# -------------------- Game Logic --------------------
if (db.reference("lawsuit_expected_players").get() or 0) <= 0:
    st.info("⚠️ Game not configured yet. Admin needs to set expected number of players.")
    st.stop()

st.header("📖 Simple Explanation of the Game")
st.markdown("""
This is a **dynamic signaling game** between two players:

🏢 **eBay** (the sender of the signal/offer)  
📡 **AT&T** (the receiver, who decides whether to accept or reject the offer)

### 🎯 What's happening?
1. **Nature decides** whether eBay is **guilty (25%)** or **innocent (75%)**
2. **eBay makes a settlement offer** to AT&T:
   - **Generous offer (G)**
   - **Stingy offer (S)**
3. **If eBay offers generous** → AT&T automatically accepts
4. **If eBay offers stingy** → AT&T chooses to either:
   - **Accept (A)** → no trial
   - **Reject (R)** → go to court

### 💰 Payoff Matrix (eBay's payoff, AT&T's payoff):

**If eBay is Guilty (25% probability):**
- Generous → Accept: (-200, 200)
- Stingy → Accept: (-20, 20)  
- Stingy → Reject (Trial): (-320, 300)

**If eBay is Innocent (75% probability):**
- Generous → Accept: (-200, 200)
- Stingy → Accept: (-20, 20)
- Stingy → Reject (Trial): (0, -20)  *(AT&T loses failed trial)*

### 🎮 Game Steps:
**Step 1**: Player Registration  
**Step 2**: Random Nature Draw (guilty/innocent hidden from AT&T)  
**Step 3**: eBay's Move – Choose settlement offer (both types can choose either offer)  
**Step 4**: AT&T's Response – Accept or reject stingy offers (generous offers auto‑accepted)  
**Step 5**: Show Results  
**Step 6**: Summary Analysis
""")

# Registration
name = st.text_input("Enter your name to join the game:")
if name:
    name = name.strip()
    player_ref = db.reference(f"lawsuit_players/{name}")
    player_data = player_ref.get()
    is_new = not player_data or "joined" not in player_data

    if is_new:
        registrations_full = db.reference("lawsuit_registrations_full").get() or False
        if registrations_full:
            st.error("❌ Registrations are closed because the expected number of players has been reached.")
            st.stop()
        else:
            player_ref.set({"joined": True, "timestamp": time.time()})
            st.success(f"👋 Welcome, {name}!")
            st.write("✅ You are registered!")
            expected = db.reference("lawsuit_expected_players").get() or 0
            new_count = len(db.reference("lawsuit_players").get() or {})
            if new_count >= expected:
                db.reference("lawsuit_registrations_full").set(True)
            st.rerun()
    else:
        st.success(f"👋 Welcome back, {name}!")

    # Wait for roles to be assigned by admin
    roles_assigned = db.reference("lawsuit_roles_assigned").get()
    if not roles_assigned:
        st.info("⏳ Waiting for admin to assign roles... (The game will start automatically once roles are assigned.)")
        time.sleep(3)
        st.rerun()

    # Wait for matching to be done by admin
    matching_done = db.reference("lawsuit_matching_done").get()
    if not matching_done:
        st.info("⏳ Waiting for admin to start matching... (Admin will pair players after roles are assigned.)")
        time.sleep(3)
        st.rerun()

    # Retrieve player's role and guilt status (if eBay)
    player_info = player_ref.get()
    if not player_info or "role" not in player_info:
        st.error("Role not found. Please ask the admin to reassign roles.")
        st.stop()
    role = player_info["role"]

    if role == "eBay":
        guilt_status = player_info.get("guilt_status")
        st.success(f"🏢 **You are eBay (the sender)**")
        if guilt_status:
            st.info(f"🎴 **Step 2 - Nature's Decision**: Your type is **{guilt_status}** (This information is private - AT&T doesn't know this)")
        else:
            st.error("Guilt status missing. Please ask admin to reassign roles.")
            st.stop()
    elif role == "AT&T":
        st.success(f"📡 **You are AT&T (the receiver)**")
    else:
        st.error("Invalid role. Please ask admin to reassign roles.")
        st.stop()

    # Get the match for this player
    matches_ref = db.reference("lawsuit_matches")
    all_matches = matches_ref.get() or {}
    player_match_id = None
    for match_id, match_data in all_matches.items():
        if name in [match_data.get("ebay_player"), match_data.get("att_player")]:
            player_match_id = match_id
            break

    if not player_match_id:
        st.info("⏳ Waiting for admin to start matching...")
        time.sleep(2)
        st.rerun()

    # Gameplay
    match_ref = matches_ref.child(player_match_id)
    match_data = match_ref.get()

    if role == "eBay":
        st.subheader("💼 Step 3: eBay's Move - Make Your Settlement Offer")
        if "ebay_response" not in match_data:
            guilt_status = match_data["ebay_guilt"]
            st.write(f"**Reminder**: You are {guilt_status}")
            st.info("💰 **Your Choice**: You can choose either a Generous or a Stingy offer.")
            offer_options = ["Generous", "Stingy"]
            offer = st.radio("Choose your settlement offer:", offer_options, help="Generous = High settlement amount, Stingy = Low settlement amount")
            if st.button("Submit Offer"):
                match_ref.update({"ebay_response": offer, "ebay_timestamp": time.time()})
                st.success(f"✅ You offered a {offer} settlement!")
                st.rerun()
        else:
            st.success(f"✅ You already submitted: {match_data['ebay_response']} offer")
            st.info("⏳ Waiting for AT&T's response...")
            if "att_response" not in match_data:
                time.sleep(2)
                st.rerun()

    elif role == "AT&T":
        st.subheader("📡 Step 4: AT&T's Response - Accept or Reject")
        if "ebay_response" not in match_data:
            st.info("⏳ Waiting for eBay to make an offer...")
            time.sleep(2)
            st.rerun()
        elif "att_response" not in match_data:
            ebay_offer = match_data["ebay_response"]
            ebay_player = match_data["ebay_player"]
            st.info(f"💼 **{ebay_player} offered a {ebay_offer} settlement**")
            if ebay_offer == "Generous":
                st.success("💰 **Game Rule**: Generous offers are automatically accepted!")
                response = "Accept"
                auto_accept = True
            else:  # Stingy
                st.write("🤔 **Strategic Decision**: You received a stingy offer. What should you infer?")
                response = st.radio("What do you do?", ["Accept", "Reject (Go to Court)"], help="Accept = Take the low settlement, Reject = Go to expensive trial")
                auto_accept = False
            if st.button("Submit Response") or auto_accept:
                response_final = "Accept" if response == "Accept" else "Reject"
                match_ref.update({"att_response": response_final, "att_timestamp": time.time()})
                st.success(f"✅ You chose to {response_final}!")
                st.rerun()
        else:
            st.success(f"✅ You responded: {match_data['att_response']}")

    # Show results when both have moved
    if "ebay_response" in match_data and "att_response" in match_data:
        st.header("🎯 Step 5: Results - The Truth is Revealed!")
        ebay_player = match_data["ebay_player"]
        att_player = match_data["att_player"]
        guilt = match_data["ebay_guilt"]
        offer = match_data["ebay_response"]
        response = match_data["att_response"]

        st.subheader("🔍 What Really Happened:")
        col1, col2, col3 = st.columns(3)
        with col1: st.info(f"**eBay's Type**\n{guilt}")
        with col2: st.info(f"**eBay's Offer**\n{offer}")
        with col3: st.info(f"**AT&T's Response**\n{response}")

        # Calculate payoffs
        if guilt == "Guilty":
            if offer == "Generous" and response == "Accept":
                ebay_payoff, att_payoff = -200, 200
            elif offer == "Stingy" and response == "Accept":
                ebay_payoff, att_payoff = -20, 20
            else:  # Stingy + Reject
                ebay_payoff, att_payoff = -320, 300
        else:  # Innocent
            if offer == "Generous" and response == "Accept":
                ebay_payoff, att_payoff = -200, 200
            elif offer == "Stingy" and response == "Accept":
                ebay_payoff, att_payoff = -20, 20
            else:  # Stingy + Reject
                ebay_payoff, att_payoff = 0, -20

        st.subheader("💰 Final Payoffs:")
        col1, col2 = st.columns(2)
        with col1: st.success(f"**eBay ({ebay_player})**\nPayoff: {ebay_payoff}")
        with col2: st.success(f"**AT&T ({att_player})**\nPayoff: {att_payoff}")

        if response == "Reject":
            st.write("⚖️ **Outcome**: Went to court! Both sides paid legal fees.")
            if guilt == "Guilty":
                st.write("🔍 **Court Result**: eBay was found guilty and paid damages plus legal costs")
            else:
                st.write("🔍 **Court Result**: eBay was found innocent - AT&T paid all legal costs!")
        else:
            st.write("🤝 **Outcome**: Settled out of court - no legal fees!")
            st.write(f"💸 **Settlement**: AT&T accepted the {offer.lower()} offer")

        st.balloons()
        st.success("✅ Your match is complete! Thank you for playing.")

        # --- Step 6: Summary Analysis for ALL players (only Theory vs Your Class Results, no deltas) ---
        st.header("📊 Step 6: Summary Analysis - Class Results vs Game Theory")
        all_matches = db.reference("lawsuit_matches").get() or {}
        completed_results = []
        for match_data in all_matches.values():
            if "ebay_response" in match_data and "att_response" in match_data:
                completed_results.append({
                    "guilt": match_data["ebay_guilt"],
                    "offer": match_data["ebay_response"],
                    "response": match_data["att_response"]
                })
        if len(completed_results) >= 1:
            guilty_offers = [r["offer"] for r in completed_results if r["guilt"] == "Guilty"]
            innocent_offers = [r["offer"] for r in completed_results if r["guilt"] == "Innocent"]
            stingy_responses = [r["response"] for r in completed_results if r["offer"] == "Stingy"]

            st.subheader("🧮 Theory vs Your Class Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                if stingy_responses:
                    accept_pct = len([r for r in stingy_responses if r == "Accept"]) / len(stingy_responses) * 100
                    st.metric("AT&T Accept Stingy Offers", f"{accept_pct:.1f}%")
                else:
                    st.metric("AT&T Accept Stingy Offers", "N/A")
            with col2:
                if guilty_offers:
                    guilty_stingy_pct = len([o for o in guilty_offers if o == "Stingy"]) / len(guilty_offers) * 100
                    st.metric("Guilty eBay Choose Stingy", f"{guilty_stingy_pct:.1f}%")
                else:
                    st.metric("Guilty eBay Choose Stingy", "N/A")
            with col3:
                if innocent_offers:
                    innocent_stingy_pct = len([o for o in innocent_offers if o == "Stingy"]) / len(innocent_offers) * 100
                    st.metric("Innocent eBay Choose Stingy", f"{innocent_stingy_pct:.1f}%")
                else:
                    st.metric("Innocent eBay Choose Stingy", "N/A")
            
            if st.button("🔄 Refresh Results"):
                st.rerun()
        else:
            st.info("Waiting for more matches to complete before showing class results...")

# Sidebar status
st.sidebar.header("🎮 Game Status")
try:
    players = db.reference("lawsuit_players").get() or {}
    expected = db.reference("lawsuit_expected_players").get() or 0
except:
    players = {}
    expected = 0
registered = len(players)
st.sidebar.write(f"**Players**: {registered}/{expected}")
if expected > 0:
    st.sidebar.progress(min(registered / expected, 1.0))
