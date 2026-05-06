// Command libp2p_peer_probe runs a minimal libp2p host with mDNS discovery and
// prints JSON lines for local peer discovery and connection events (stdout).
//
//	go run . [--service-name tag]
//
// Track B in docs/DISCOVERY_PLAN.md — independent of SIL TCP and LAN _fieldlight._tcp.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/libp2p/go-libp2p"
	"github.com/libp2p/go-libp2p/core/network"
	"github.com/libp2p/go-libp2p/core/peer"
	"github.com/libp2p/go-libp2p/p2p/discovery/mdns"
	ma "github.com/multiformats/go-multiaddr"
)

func main() {
	serviceName := flag.String("service-name", "fieldlight-libp2p", "mDNS service tag for local peer discovery")
	flag.Parse()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	host, err := libp2p.New()
	if err != nil {
		fmt.Fprintf(os.Stderr, "host: %v\n", err)
		os.Exit(1)
	}
	defer host.Close()

	emit("host_started", map[string]any{
		"id":    host.ID().String(),
		"addrs": addrStrings(host.Addrs()),
	})

	host.Network().Notify(&network.NotifyBundle{
		ConnectedF: func(_ network.Network, c network.Conn) {
			emit("connected", map[string]any{
				"remote_peer": c.RemotePeer().String(),
				"remote_addr": c.RemoteMultiaddr().String(),
			})
		},
		DisconnectedF: func(_ network.Network, c network.Conn) {
			emit("disconnected", map[string]any{
				"remote_peer": c.RemotePeer().String(),
			})
		},
	})

	disc := mdns.NewMdnsService(host, *serviceName, mdnsNotifee{})
	defer disc.Close()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	select {
	case <-sig:
	case <-ctx.Done():
	}
}

type mdnsNotifee struct{}

func (mdnsNotifee) HandlePeerFound(pi peer.AddrInfo) {
	emit("mdns_peer_found", map[string]any{
		"id":    pi.ID.String(),
		"addrs": addrStrings(pi.Addrs),
	})
}

func emit(event string, fields map[string]any) {
	fields["event"] = event
	fields["ts"] = time.Now().UTC().Format(time.RFC3339Nano)
	_ = json.NewEncoder(os.Stdout).Encode(fields)
}

func addrStrings(addrs []ma.Multiaddr) []string {
	out := make([]string, 0, len(addrs))
	for _, a := range addrs {
		if a != nil {
			out = append(out, a.String())
		}
	}
	return out
}
