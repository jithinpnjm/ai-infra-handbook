package main

import (
	"fmt"
	"os"

	"github.com/stmcginnis/gofish"
	"github.com/stmcginnis/gofish/schemas"
)

func main() {
	cfg := gofish.ClientConfig{Endpoint: os.Args[1], Username: "admin", Password: "adminpass", Insecure: true}
	c, err := gofish.Connect(cfg)
	if err != nil { fmt.Println("connect:", err); os.Exit(1) }
	defer c.Logout()
	svc := c.GetService()
	systems, err := svc.Systems()
	if err != nil { fmt.Println("systems:", err); os.Exit(1) }
	for _, s := range systems {
		fmt.Println(s.ID, s.PowerState, s.Status.Health)
	}
	if len(os.Args) > 2 {
		if _, err := systems[0].Reset(schemas.GracefulRestartResetType); err != nil { fmt.Println("reset:", err) } else { fmt.Println("reset sent") }
	}
}
