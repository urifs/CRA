"""
Test suite for RH Ponto Eletrônico, Folha de Pagamento, and Custos endpoints
Tests:
- Ponto Eletrônico: GET /api/rh/ponto, POST /api/rh/ponto, GET /api/rh/ponto/relatorio-mensal, POST /api/rh/ponto/registrar-rapido
- Folha de Pagamento: GET /api/rh/folha-pagamento, POST /api/rh/folha-pagamento, GET /api/rh/folha-pagamento/{id}/holerite, POST /api/rh/folha-pagamento/gerar-contas-pagar
- Custos RH: GET /api/rh/custos, POST /api/rh/custos/simular-dissidio, POST /api/rh/custos/simular-rescisao
"""

import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://erp-fixes-preview.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "password"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def funcionarios(auth_headers):
    """Get list of active funcionarios"""
    response = requests.get(f"{BASE_URL}/api/rh/funcionarios?status=ativo", headers=auth_headers)
    assert response.status_code == 200
    return response.json()


class TestPontoEletronico:
    """Tests for Ponto Eletrônico endpoints"""
    
    def test_list_ponto_by_date(self, auth_headers):
        """GET /api/rh/ponto - List ponto records by date"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/rh/ponto?data={today}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "registros" in data
        assert "resumo" in data
        assert isinstance(data["registros"], list)
        assert "presentes" in data["resumo"]
        assert "ausentes" in data["resumo"]
        assert "atrasados" in data["resumo"]
        print(f"✓ Ponto list returned {len(data['registros'])} records for {today}")
        print(f"  Resumo: {data['resumo']}")
    
    def test_create_ponto_record(self, auth_headers, funcionarios):
        """POST /api/rh/ponto - Create ponto record"""
        if not funcionarios:
            pytest.skip("No funcionarios available for testing")
        
        funcionario = funcionarios[0]
        # Use a date in the past to avoid conflicts
        test_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # First, try to delete any existing record for this date
        response = requests.get(f"{BASE_URL}/api/rh/ponto?data={test_date}&funcionario_id={funcionario['id']}", headers=auth_headers)
        if response.status_code == 200:
            existing = response.json().get("registros", [])
            for reg in existing:
                requests.delete(f"{BASE_URL}/api/rh/ponto/{reg['id']}", headers=auth_headers)
        
        # Create new ponto record
        ponto_data = {
            "funcionario_id": funcionario["id"],
            "data": test_date,
            "entrada": "08:00",
            "saida_almoco": "11:30",
            "retorno_almoco": "13:30",
            "saida": "18:00",
            "observacoes": "TEST_ponto_record"
        }
        
        response = requests.post(f"{BASE_URL}/api/rh/ponto", json=ponto_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to create ponto: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["funcionario_id"] == funcionario["id"]
        assert data["data"] == test_date
        assert data["entrada"] == "08:00"
        print(f"✓ Created ponto record for {funcionario['nome']} on {test_date}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/rh/ponto/{data['id']}", headers=auth_headers)
    
    def test_create_ponto_duplicate_fails(self, auth_headers, funcionarios):
        """POST /api/rh/ponto - Duplicate ponto should fail"""
        if not funcionarios:
            pytest.skip("No funcionarios available for testing")
        
        funcionario = funcionarios[0]
        test_date = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d")
        
        # Clean up first
        response = requests.get(f"{BASE_URL}/api/rh/ponto?data={test_date}&funcionario_id={funcionario['id']}", headers=auth_headers)
        if response.status_code == 200:
            existing = response.json().get("registros", [])
            for reg in existing:
                requests.delete(f"{BASE_URL}/api/rh/ponto/{reg['id']}", headers=auth_headers)
        
        ponto_data = {
            "funcionario_id": funcionario["id"],
            "data": test_date,
            "entrada": "08:00",
            "saida": "18:00",
            "observacoes": "TEST_duplicate"
        }
        
        # Create first record
        response1 = requests.post(f"{BASE_URL}/api/rh/ponto", json=ponto_data, headers=auth_headers)
        assert response1.status_code == 200
        created_id = response1.json()["id"]
        
        # Try to create duplicate
        response2 = requests.post(f"{BASE_URL}/api/rh/ponto", json=ponto_data, headers=auth_headers)
        assert response2.status_code == 400
        assert "Já existe registro" in response2.json().get("detail", "")
        print("✓ Duplicate ponto correctly rejected")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/rh/ponto/{created_id}", headers=auth_headers)
    
    def test_relatorio_mensal(self, auth_headers):
        """GET /api/rh/ponto/relatorio-mensal - Monthly report with overtime"""
        mes = datetime.now().month
        ano = datetime.now().year
        
        response = requests.get(f"{BASE_URL}/api/rh/ponto/relatorio-mensal?mes={mes}&ano={ano}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mes" in data
        assert "ano" in data
        assert "funcionarios" in data
        assert "total_funcionarios" in data
        assert data["mes"] == mes
        assert data["ano"] == ano
        
        # Check funcionario report structure if any
        if data["funcionarios"]:
            func_report = data["funcionarios"][0]
            assert "funcionario_id" in func_report
            assert "nome" in func_report
            assert "horas_trabalhadas" in func_report
            assert "horas_extras" in func_report
            assert "valor_horas_extras" in func_report
        
        print(f"✓ Monthly report returned {data['total_funcionarios']} funcionarios for {mes}/{ano}")
    
    def test_registrar_rapido(self, auth_headers, funcionarios):
        """POST /api/rh/ponto/registrar-rapido - Quick registration"""
        if not funcionarios:
            pytest.skip("No funcionarios available for testing")
        
        funcionario = funcionarios[0]
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        # Clean up any existing record for today
        response = requests.get(f"{BASE_URL}/api/rh/ponto?data={hoje}&funcionario_id={funcionario['id']}", headers=auth_headers)
        if response.status_code == 200:
            existing = response.json().get("registros", [])
            for reg in existing:
                requests.delete(f"{BASE_URL}/api/rh/ponto/{reg['id']}", headers=auth_headers)
        
        # Test quick entry registration
        response = requests.post(
            f"{BASE_URL}/api/rh/ponto/registrar-rapido",
            json={"funcionario_id": funcionario["id"], "tipo": "entrada"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "registro" in data
        assert "Entrada" in data["message"]
        print(f"✓ Quick registration successful: {data['message']}")
        
        # Cleanup
        if data.get("registro", {}).get("id"):
            requests.delete(f"{BASE_URL}/api/rh/ponto/{data['registro']['id']}", headers=auth_headers)


class TestFolhaPagamento:
    """Tests for Folha de Pagamento endpoints"""
    
    def test_list_folha_pagamento(self, auth_headers):
        """GET /api/rh/folha-pagamento - List payroll by month/year"""
        mes = 2
        ano = 2026
        
        response = requests.get(f"{BASE_URL}/api/rh/folha-pagamento?mes={mes}&ano={ano}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check structure if any folhas exist
        if data:
            folha = data[0]
            assert "id" in folha
            assert "funcionario_id" in folha
            assert "mes" in folha
            assert "ano" in folha
            assert "salario_bruto" in folha
            assert "inss" in folha
            assert "irpf" in folha
            assert "fgts" in folha
            assert "salario_liquido" in folha
        
        print(f"✓ Folha pagamento list returned {len(data)} records for {mes}/{ano}")
    
    def test_create_folha_pagamento(self, auth_headers, funcionarios):
        """POST /api/rh/folha-pagamento - Create payroll with calculations"""
        if not funcionarios:
            pytest.skip("No funcionarios available for testing")
        
        funcionario = funcionarios[0]
        # Use a test month that won't conflict
        test_mes = 1
        test_ano = 2025
        
        # Clean up any existing folha for this period
        response = requests.get(f"{BASE_URL}/api/rh/folha-pagamento?mes={test_mes}&ano={test_ano}", headers=auth_headers)
        if response.status_code == 200:
            existing = response.json()
            for folha in existing:
                if folha.get("funcionario_id") == funcionario["id"]:
                    requests.delete(f"{BASE_URL}/api/rh/folha-pagamento/{folha['id']}", headers=auth_headers)
        
        # Calculate expected values
        salario_base = funcionario.get("salario", 3500)
        inss = min(salario_base * 0.12, 951.01)  # Simplified INSS calculation
        irpf = max(0, (salario_base - inss - 2259.20) * 0.075)  # Simplified IRPF
        fgts = salario_base * 0.08
        total_descontos = inss + irpf
        salario_liquido = salario_base - total_descontos
        
        folha_data = {
            "funcionario_id": funcionario["id"],
            "mes": test_mes,
            "ano": test_ano,
            "salario_base": salario_base,
            "horas_extras": 0,
            "valor_hora_extra": 0,
            "adicional_noturno": 0,
            "comissoes": 0,
            "vale_transporte": 0,
            "vale_alimentacao": 0,
            "plano_saude": 0,
            "outros_descontos": 0,
            "observacoes": "TEST_folha",
            "salario_bruto": salario_base,
            "inss": inss,
            "irpf": irpf,
            "fgts": fgts,
            "total_descontos": total_descontos,
            "salario_liquido": salario_liquido
        }
        
        response = requests.post(f"{BASE_URL}/api/rh/folha-pagamento", json=folha_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to create folha: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["funcionario_id"] == funcionario["id"]
        assert data["mes"] == test_mes
        assert data["ano"] == test_ano
        assert data["salario_bruto"] == salario_base
        assert data["fgts"] == fgts
        print(f"✓ Created folha pagamento for {funcionario['nome']} - {test_mes}/{test_ano}")
        print(f"  Salário Bruto: R$ {data['salario_bruto']:.2f}, INSS: R$ {data['inss']:.2f}, Líquido: R$ {data['salario_liquido']:.2f}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/rh/folha-pagamento/{data['id']}", headers=auth_headers)
    
    def test_generate_holerite_pdf(self, auth_headers):
        """GET /api/rh/folha-pagamento/{id}/holerite - Generate PDF"""
        # Use existing folha from February 2026
        folha_id = "bc6afc49-7d33-4b6b-a069-3c87127b0640"
        
        response = requests.get(f"{BASE_URL}/api/rh/folha-pagamento/{folha_id}/holerite", headers=auth_headers)
        
        # Should return PDF or 404 if folha doesn't exist
        if response.status_code == 200:
            assert response.headers.get("content-type") == "application/pdf"
            assert len(response.content) > 0
            print(f"✓ Holerite PDF generated successfully ({len(response.content)} bytes)")
        elif response.status_code == 404:
            print("⚠ Folha not found - skipping PDF test")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_gerar_contas_pagar(self, auth_headers):
        """POST /api/rh/folha-pagamento/gerar-contas-pagar - Generate accounts payable"""
        mes = 2
        ano = 2026
        
        response = requests.post(
            f"{BASE_URL}/api/rh/folha-pagamento/gerar-contas-pagar",
            json={"mes": mes, "ano": ano},
            headers=auth_headers
        )
        
        # Should succeed if folhas exist, or return 400 if no folhas
        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "contas_criadas" in data
            assert "total" in data or "contas_criadas" in data
            print(f"✓ Contas a pagar generated: {data.get('message', data.get('contas_criadas', []))}")
        elif response.status_code == 400:
            assert "Nenhuma folha encontrada" in response.json().get("detail", "")
            print("⚠ No folhas found for this period - expected behavior")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code} - {response.text}")


class TestCustosRH:
    """Tests for Custos RH endpoints"""
    
    def test_get_custos(self, auth_headers):
        """GET /api/rh/custos - List costs by employee"""
        response = requests.get(f"{BASE_URL}/api/rh/custos", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "funcionarios" in data
        assert "resumo" in data
        assert isinstance(data["funcionarios"], list)
        
        # Check resumo structure
        resumo = data["resumo"]
        assert "total_salarios" in resumo
        assert "total_encargos" in resumo
        assert "total_beneficios" in resumo
        assert "total_epis" in resumo
        assert "custo_total" in resumo
        
        # Check funcionario cost structure if any
        if data["funcionarios"]:
            func_cost = data["funcionarios"][0]
            assert "funcionario_id" in func_cost
            assert "nome" in func_cost
            assert "salario" in func_cost
            assert "fgts" in func_cost
            assert "inss_patronal" in func_cost
            assert "beneficios" in func_cost
            assert "epis" in func_cost
            assert "custo_total" in func_cost
            assert "custo_hora" in func_cost
            
            # Verify FGTS is 8%
            expected_fgts = func_cost["salario"] * 0.08
            assert abs(func_cost["fgts"] - expected_fgts) < 0.01, f"FGTS should be 8%: expected {expected_fgts}, got {func_cost['fgts']}"
            
            # Verify INSS Patronal is 20%
            expected_inss = func_cost["salario"] * 0.20
            assert abs(func_cost["inss_patronal"] - expected_inss) < 0.01, f"INSS Patronal should be 20%: expected {expected_inss}, got {func_cost['inss_patronal']}"
        
        print(f"✓ Custos RH returned {len(data['funcionarios'])} funcionarios")
        print(f"  Total Salários: R$ {resumo['total_salarios']:.2f}")
        print(f"  Total Encargos: R$ {resumo['total_encargos']:.2f}")
        print(f"  Custo Total: R$ {resumo['custo_total']:.2f}")
    
    def test_simular_dissidio(self, auth_headers):
        """POST /api/rh/custos/simular-dissidio - Simulate collective bargaining impact"""
        percentual = 5.0
        
        response = requests.post(
            f"{BASE_URL}/api/rh/custos/simular-dissidio",
            json={"percentual": percentual},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "percentual" in data
        assert "folha_atual" in data
        assert "folha_com_dissidio" in data
        assert "impacto_mensal" in data
        assert "impacto_anual" in data
        
        assert data["percentual"] == percentual
        
        # Verify calculations
        expected_folha_dissidio = data["folha_atual"] * (1 + percentual / 100)
        assert abs(data["folha_com_dissidio"] - expected_folha_dissidio) < 0.01
        
        expected_impacto_mensal = data["folha_com_dissidio"] - data["folha_atual"]
        assert abs(data["impacto_mensal"] - expected_impacto_mensal) < 0.01
        
        expected_impacto_anual = expected_impacto_mensal * 12
        assert abs(data["impacto_anual"] - expected_impacto_anual) < 0.01
        
        print(f"✓ Dissídio simulation ({percentual}%):")
        print(f"  Folha Atual: R$ {data['folha_atual']:.2f}")
        print(f"  Folha com Dissídio: R$ {data['folha_com_dissidio']:.2f}")
        print(f"  Impacto Mensal: R$ {data['impacto_mensal']:.2f}")
        print(f"  Impacto Anual: R$ {data['impacto_anual']:.2f}")
    
    def test_simular_rescisao(self, auth_headers, funcionarios):
        """POST /api/rh/custos/simular-rescisao - Calculate termination provision"""
        if not funcionarios:
            pytest.skip("No funcionarios available for testing")
        
        funcionario = funcionarios[0]
        
        response = requests.post(
            f"{BASE_URL}/api/rh/custos/simular-rescisao",
            json={"funcionario_id": funcionario["id"]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "funcionario" in data
        assert "meses_trabalhados" in data
        assert "salario" in data
        assert "saldo_salario" in data
        assert "dias_aviso_previo" in data
        assert "aviso_previo" in data
        assert "ferias_vencidas" in data
        assert "ferias_proporcionais" in data
        assert "decimo_terceiro" in data
        assert "fgts_saldo" in data
        assert "multa_fgts" in data
        assert "total" in data
        
        # Verify FGTS multa is 40%
        expected_multa = data["fgts_saldo"] * 0.4
        assert abs(data["multa_fgts"] - expected_multa) < 0.01, f"Multa FGTS should be 40%"
        
        # Verify aviso prévio calculation (30 + 3 per year, max 90)
        anos = data["meses_trabalhados"] // 12
        expected_dias = min(30 + (anos * 3), 90)
        assert data["dias_aviso_previo"] == expected_dias
        
        print(f"✓ Rescisão simulation for {data['funcionario']}:")
        print(f"  Meses Trabalhados: {data['meses_trabalhados']}")
        print(f"  Aviso Prévio ({data['dias_aviso_previo']} dias): R$ {data['aviso_previo']:.2f}")
        print(f"  FGTS Saldo: R$ {data['fgts_saldo']:.2f}")
        print(f"  Multa FGTS (40%): R$ {data['multa_fgts']:.2f}")
        print(f"  Total Rescisão: R$ {data['total']:.2f}")
    
    def test_simular_rescisao_funcionario_not_found(self, auth_headers):
        """POST /api/rh/custos/simular-rescisao - Should return 404 for invalid funcionario"""
        response = requests.post(
            f"{BASE_URL}/api/rh/custos/simular-rescisao",
            json={"funcionario_id": "invalid-id-12345"},
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "não encontrado" in response.json().get("detail", "").lower()
        print("✓ Invalid funcionario correctly returns 404")


class TestPontoUpdate:
    """Tests for Ponto update and delete operations"""
    
    def test_update_ponto(self, auth_headers, funcionarios):
        """PUT /api/rh/ponto/{id} - Update ponto record"""
        if not funcionarios:
            pytest.skip("No funcionarios available for testing")
        
        funcionario = funcionarios[0]
        test_date = (datetime.now() - timedelta(days=32)).strftime("%Y-%m-%d")
        
        # Clean up first
        response = requests.get(f"{BASE_URL}/api/rh/ponto?data={test_date}&funcionario_id={funcionario['id']}", headers=auth_headers)
        if response.status_code == 200:
            existing = response.json().get("registros", [])
            for reg in existing:
                requests.delete(f"{BASE_URL}/api/rh/ponto/{reg['id']}", headers=auth_headers)
        
        # Create a record
        ponto_data = {
            "funcionario_id": funcionario["id"],
            "data": test_date,
            "entrada": "08:00",
            "saida": "17:00",
            "observacoes": "TEST_update"
        }
        
        response = requests.post(f"{BASE_URL}/api/rh/ponto", json=ponto_data, headers=auth_headers)
        assert response.status_code == 200
        ponto_id = response.json()["id"]
        
        # Update the record
        updated_data = {
            "funcionario_id": funcionario["id"],
            "data": test_date,
            "entrada": "08:30",
            "saida": "18:00",
            "observacoes": "TEST_updated"
        }
        
        response = requests.put(f"{BASE_URL}/api/rh/ponto/{ponto_id}", json=updated_data, headers=auth_headers)
        assert response.status_code == 200
        print("✓ Ponto record updated successfully")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/rh/ponto/{ponto_id}", headers=auth_headers)
    
    def test_delete_ponto(self, auth_headers, funcionarios):
        """DELETE /api/rh/ponto/{id} - Delete ponto record"""
        if not funcionarios:
            pytest.skip("No funcionarios available for testing")
        
        funcionario = funcionarios[0]
        test_date = (datetime.now() - timedelta(days=33)).strftime("%Y-%m-%d")
        
        # Clean up first
        response = requests.get(f"{BASE_URL}/api/rh/ponto?data={test_date}&funcionario_id={funcionario['id']}", headers=auth_headers)
        if response.status_code == 200:
            existing = response.json().get("registros", [])
            for reg in existing:
                requests.delete(f"{BASE_URL}/api/rh/ponto/{reg['id']}", headers=auth_headers)
        
        # Create a record
        ponto_data = {
            "funcionario_id": funcionario["id"],
            "data": test_date,
            "entrada": "08:00",
            "saida": "17:00",
            "observacoes": "TEST_delete"
        }
        
        response = requests.post(f"{BASE_URL}/api/rh/ponto", json=ponto_data, headers=auth_headers)
        assert response.status_code == 200
        ponto_id = response.json()["id"]
        
        # Delete the record
        response = requests.delete(f"{BASE_URL}/api/rh/ponto/{ponto_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "excluído" in response.json().get("message", "").lower()
        print("✓ Ponto record deleted successfully")
    
    def test_delete_ponto_not_found(self, auth_headers):
        """DELETE /api/rh/ponto/{id} - Should return 404 for invalid id"""
        response = requests.delete(f"{BASE_URL}/api/rh/ponto/invalid-id-12345", headers=auth_headers)
        assert response.status_code == 404
        print("✓ Invalid ponto delete correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
